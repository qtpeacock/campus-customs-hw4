"""Campus Customs API: products, accounts, and the shop chatbot.

Run from backend/:  uvicorn main:app --reload --port 8000
API docs:           http://127.0.0.1:8000/docs
Frontend:           http://127.0.0.1:5173 (Vite proxies /api and /images here)

The chatbot is a PydanticAI agent made of four files next to this one:
prompts/prompt.md (system prompt), agent.py (wiring), tools.py (tools), and
models.py (structured types).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import HISTORY_TURNS, AgentNotConfigured, draft_cart_reminders, model_name, run_chat
from models import (
    CartChange,
    CartItemRequest,
    CartItemsRequest,
    CartView,
    ChatHistory,
    ChatRequest,
    ChatResponse,
    ChatTurn,
    CustomerProfile,
    LoginRequest,
    OutboxEmail,
    PageSearch,
    PreferencesRequest,
    RegisterRequest,
    StoredChatMessage,
    UserOut,
)
from tools import (
    WORN_IMAGES,
    ShopDeps,
    cart_add,
    cart_merge,
    cart_preview,
    cart_remove,
    cart_set_quantity,
    create_cart_tables,
    extra_image_urls,
    garment_kind,
    has_real_description,
    get_cart,
    image_url,
    list_outbox,
    page_matches,
    product_cards,
    product_collections,
    resolve_page,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

SESSION_COOKIE = "cc_session"
HISTORY_SHOWN = 50  # saved messages the chat panel reloads for a returning shopper
# Set COOKIE_SECURE=true when the site is served over HTTPS.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# ==================== Security: passwords, sessions, rate limits ====================
# Password hashing, login sessions, and rate limits for Campus Customs.
#
# Passwords
#     PBKDF2-HMAC-SHA256 with a random 16-byte salt per user and 600,000
#     iterations (OWASP's current recommendation), stored as
#         pbkdf2_sha256$<iterations>$<salt>$<hex digest>
#     The seed users were stored as pbkdf2_sha256$<salt>$<hex digest> with a fixed
#     120,000 iterations. Those still verify, and are re-hashed at full strength
#     the next time that user logs in.
#
# Sessions
#     A random 256-bit token goes to the browser in an HttpOnly cookie. The
#     database keeps only the token's SHA-256 hash, so a copy of the database
#     can't be used to take over anyone's login.

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000
SALT_BYTES = 16
SESSION_DAYS = 7


# ---------- Passwords ----------


def _pbkdf2(password: str, salt: str, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)


def hash_password(password: str) -> str:
    """Hash a new password with a fresh random salt."""
    salt = secrets.token_hex(SALT_BYTES)
    digest = _pbkdf2(password, salt, ITERATIONS).hex()
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    """Return (iterations, salt, digest) for either stored format, or None if unrecognised."""
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == ALGORITHM and parts[1].isdigit():
        return int(parts[1]), parts[2], parts[3]
    if len(parts) == 3 and parts[0] == ALGORITHM:
        return LEGACY_ITERATIONS, parts[1], parts[2]
    return None


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash using a constant-time comparison."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    iterations, salt, digest = parsed
    return hmac.compare_digest(_pbkdf2(password, salt, iterations).hex(), digest)


def needs_rehash(stored: str) -> bool:
    """True for hashes weaker than the current settings (e.g. the 120,000-iteration seed format)."""
    parsed = _parse(stored)
    return parsed is None or parsed[0] < ITERATIONS


# Checked when an email isn't found, so "no such account" takes as long as
# "wrong password" and response timing doesn't reveal which emails exist.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


def burn_equal_time(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


# ---------- Sessions ----------


def new_session_token() -> tuple[str, str]:
    """Return (token for the cookie, hash for the database)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------- Rate limits ----------


class WindowLimiter:
    """Counts events per key (an email or an IP address) in a sliding window and blocks at a limit.

    Used for failed logins (brute-force protection) and for chat messages (cost and abuse control).
    """

    def __init__(self, max_events: int, window_seconds: int = 15 * 60) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _recent(self, key: str) -> deque[float]:
        events = self._events[key]
        cutoff = time.monotonic() - self.window_seconds
        while events and events[0] < cutoff:
            events.popleft()
        return events

    def blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self.max_events

    def record(self, key: str) -> None:
        self._recent(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._events.pop(key, None)


# Failed logins allowed per 15 minutes before that email / IP address is paused.
email_limiter = WindowLimiter(max_events=5)
ip_limiter = WindowLimiter(max_events=20)
# Chat messages allowed per IP address every 5 minutes (each one is a paid model call).
chat_limiter = WindowLimiter(max_events=30, window_seconds=5 * 60)

log = logging.getLogger("campus_customs")


@contextmanager
def db(write: bool = False) -> Iterator[sqlite3.Connection]:
    """Open the shop database (read-only unless write=True); commit on success, always close."""
    mode = "rw" if write else "ro"
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Login sessions live in their own table; only a hash of each token is stored.
    with db(write=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")

        # Chat history uses the chat_messages table that came with the database. One column is added so a
        # saved reply also remembers the search it put on the page (title + filters).
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(chat_messages)")}
        if "page_json" not in columns:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN page_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")

        # Saved carts, drafted reminder emails, and the users.cart_emails opt-in (see tools.py).
        create_cart_tables(conn)
    yield


app = FastAPI(title="Campus Customs API", version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Only the product image folder is public; the database beside it is not.
# catalogue.image_file_path is "products/<file>.jpg", so it maps to /images/products/<file>.jpg.
# scripts/whiten_backgrounds.py writes white-background copies to data/products_white/; serve those when present.
WHITE_IMAGES = DATA_DIR / "products_white"
IMAGE_DIR = WHITE_IMAGES if WHITE_IMAGES.is_dir() else DATA_DIR / "products"
app.mount(
    "/images/products",
    StaticFiles(directory=IMAGE_DIR),
    name="product-images",
)
# Extra "worn on campus" photos for products that appeared in last homework's photos (data/worn/, not committed).
if WORN_IMAGES.is_dir():
    app.mount("/images/worn", StaticFiles(directory=WORN_IMAGES), name="worn-images")


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# ---------- Products ----------


def product_out(row: sqlite3.Row) -> dict:
    """Shape a catalogue row for the front end (JSON columns parsed, image URL built)."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        # One of six shopper-facing kinds (hoodie, crewneck, t-shirt, quarter-zip, jacket, long-sleeve),
        # used by the Products page categories; the catalogue itself spells garment types 22 ways.
        "kind": garment_kind(row["garment_type"]),
        "description": row["description"]
        if has_real_description(row["description"])
        else "We're still writing this one up. The photo shows the design.",
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        # Shop-by collections (colleges, sports, family, schools, classics) for the Products menu and page.
        "collections": product_collections(row["name"]),
        # Extra photos (a shopper wearing it), shown on hover and in the product page gallery.
        "extra_images": extra_image_urls(row["product_id"]),
    }


@app.get("/api/health")
def health():
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    return {
        "ok": True,
        "products": count,
        "chat_model": model_name(),
        "chat_configured": bool(os.getenv("PORTKEY_API_KEY")),
    }


@app.get("/api/products")
def list_products():
    """Every product in the catalogue, for the products page."""
    with db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        stock: dict[str, dict[str, int]] = {}
        for item in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            stock.setdefault(item["product_id"], {})[item["size"]] = item["quantity"]
    # Stock per size lets each card show honest badges ("Only 2 left in M") and offer quick add.
    products = [{**product_out(row), "stock": stock.get(row["product_id"], {})} for row in rows]
    return {"count": len(products), "products": products}


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    """One product with its stock for each size, for the single-item page."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    sizes = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in stock),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER),
    )
    return {**product_out(row), "sizes": sizes}


# ---------- Accounts ----------

# Every query that returns a user lists its columns, so password_hash never leaves the backend.
USER_COLUMNS = "users.id, users.name, users.first_name, users.last_name, users.email, users.cart_emails"


def user_out(row: sqlite3.Row) -> UserOut:
    """The public view of a user: no password hash, ever."""
    parts = row["name"].split(" ", 1)
    return UserOut(
        id=row["id"],
        first_name=row["first_name"] or parts[0],
        last_name=row["last_name"] or (parts[1] if len(parts) > 1 else ""),
        name=row["name"],
        email=row["email"],
        cart_emails=bool(row["cart_emails"]),
    )


def start_session(conn: sqlite3.Connection, response: Response, user_id: int) -> None:
    """Record a new session and hand its token to the browser as an HttpOnly cookie."""
    token, token_hash = new_session_token()
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, datetime('now', ?))",
        (token_hash, user_id, f"+{SESSION_DAYS} days"),
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def current_user(request: Request) -> UserOut | None:
    """The logged-in user for this request, or None."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    with db() as conn:
        row = conn.execute(
            f"""
            SELECT {USER_COLUMNS} FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > datetime('now')
            """,
            (hash_token(token),),
        ).fetchone()
    return user_out(row) if row else None


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest, response: Response):
    """Create an account in the users table and log the new shopper in."""
    email_taken = HTTPException(
        status_code=409,
        detail="An account with that email already exists. Try logging in instead.",
    )
    password_hash = hash_password(body.password)
    with db(write=True) as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (body.email,)).fetchone():
            raise email_taken
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name, cart_emails) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    f"{body.first_name} {body.last_name}",
                    body.email,
                    password_hash,
                    body.first_name,
                    body.last_name,
                    int(body.cart_emails),
                ),
            )
        except sqlite3.IntegrityError:  # two sign-ups with the same email at the same moment
            raise email_taken from None
        user_id = cursor.lastrowid
        start_session(conn, response, user_id)
        user = conn.execute(f"SELECT {USER_COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"user": user_out(user)}


@app.post("/api/auth/login")
def login(body: LoginRequest, request: Request, response: Response):
    """Check an email and password; on success start a session."""
    ip = client_ip(request)
    if email_limiter.blocked(body.email) or ip_limiter.blocked(ip):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait a few minutes and try again.",
        )

    with db() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE lower(email) = ?", (body.email,)
        ).fetchone()

    if row is None:
        burn_equal_time(body.password)
        valid = False
    else:
        valid = verify_password(body.password, row["password_hash"])

    if not valid:
        email_limiter.record(body.email)
        ip_limiter.record(ip)
        # Same message whether the email or the password was wrong.
        raise HTTPException(status_code=401, detail="That email and password don't match our records.")

    email_limiter.reset(body.email)
    with db(write=True) as conn:
        if needs_rehash(row["password_hash"]):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(body.password), row["id"]),
            )
        start_session(conn, response, row["id"])
        user = conn.execute(f"SELECT {USER_COLUMNS} FROM users WHERE id = ?", (row["id"],)).fetchone()
    return {"user": user_out(user)}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    """End the session on the server and clear the cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with db(write=True) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request):
    """Who is logged in; user is null for visitors who aren't."""
    return {"user": current_user(request)}


# ---------- Chat ----------


def customer_profile(user: UserOut) -> CustomerProfile:
    """What the agent may know about the logged-in shopper (never the password hash or session)."""
    with db() as conn:
        created = conn.execute("SELECT created_at FROM users WHERE id = ?", (user.id,)).fetchone()
        saved = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user.id,)).fetchone()[0]
    return CustomerProfile(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        name=user.name,
        email=user.email,
        member_since=(created["created_at"] if created else "")[:10],
        saved_messages=saved,
    )


def saved_product_ids(products_json: str | None) -> list[str]:
    """Product ids from a saved message (the seed rows store full product dicts; new rows store cards)."""
    if not products_json:
        return []
    try:
        items = json.loads(products_json)
    except json.JSONDecodeError:
        return []
    return [item["product_id"] for item in items if isinstance(item, dict) and item.get("product_id")]


def saved_page_search(page_json: str | None) -> PageSearch | None:
    if not page_json:
        return None
    try:
        return PageSearch.model_validate_json(page_json)
    except ValueError:
        return None


def recent_messages(user_id: int, limit: int) -> list[sqlite3.Row]:
    """A shopper's latest saved messages, oldest first. Always filtered by their own user_id."""
    with db() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, page_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def history_for_agent(user_id: int) -> list[ChatTurn]:
    """The logged-in shopper's recent turns, read from the database rather than trusted from the browser."""
    turns = []
    for row in recent_messages(user_id, HISTORY_TURNS):
        if row["role"] not in ("user", "assistant"):
            continue
        page = saved_page_search(row["page_json"])
        turns.append(
            ChatTurn(
                role=row["role"],
                content=row["content"][:4000],
                product_ids=saved_product_ids(row["products_json"])[:6],
                page_title=page.title if page else None,
            )
        )
    return turns


def save_exchange(user_id: int, message: str, response: ChatResponse, page: PageSearch | None) -> None:
    """Store the shopper's message and the assistant's reply (with its cards and page search) together."""
    with db(write=True) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_json) VALUES (?, 'assistant', ?, ?, ?)",
            (
                user_id,
                response.reply,
                json.dumps([card.model_dump() for card in response.products]),
                page.model_dump_json() if page else None,
            ),
        )


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(request: Request) -> ChatHistory:
    """The logged-in shopper's saved conversation (latest 50 messages); guests get an empty list."""
    user = current_user(request)
    if user is None:
        return ChatHistory(logged_in=False, messages=[])
    messages = []
    for row in recent_messages(user.id, HISTORY_SHOWN):
        if row["role"] not in ("user", "assistant"):
            continue
        page = saved_page_search(row["page_json"])
        messages.append(
            StoredChatMessage(
                role=row["role"],
                content=row["content"],
                # Rebuilt from the catalogue, so a reloaded card shows today's name, price, and photo.
                products=product_cards(DB_PATH, saved_product_ids(row["products_json"])),
                page_results=page_matches(DB_PATH, page) if page else None,
                created_at=row["created_at"],
            )
        )
    return ChatHistory(logged_in=True, messages=messages)


@app.delete("/api/chat/history")
def clear_chat_history(request: Request):
    """Start over: delete the logged-in shopper's saved messages (only theirs)."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to manage your saved chat.")
    with db(write=True) as conn:
        deleted = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user.id,)).rowcount
    return {"ok": True, "deleted": deleted}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Send one shopper message to the agent, with who is chatting and which page they're on.

    Logged-in shoppers: history comes from chat_messages and the new exchange is saved there.
    Guests: history comes from the browser and nothing is saved.

    Returns the reply, a few product cards for the chat, and, when the shopper is browsing a type of item,
    page_results: every matching product for the website to show on the page.
    """
    ip = client_ip(request)
    if chat_limiter.blocked(ip):
        raise HTTPException(
            status_code=429,
            detail="You're sending messages faster than I can keep up. Give it a minute and try again.",
        )
    chat_limiter.record(ip)

    user = current_user(request)
    deps = ShopDeps(
        db_path=DB_PATH,
        customer=customer_profile(user) if user else None,
        page=resolve_page(DB_PATH, body.page),
    )
    history = history_for_agent(user.id) if user else body.history
    try:
        reply = await run_chat(body.message, history, deps)
    except AgentNotConfigured:
        raise HTTPException(status_code=503, detail="The chat isn't set up on this server yet.") from None
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, I'm having trouble answering right now. Please try again in a moment.",
        ) from None

    # Everything the website shows is built from the database, so names, prices, and images are always real:
    # a few cards inside the chat, plus (for browsing questions) every match to show on the page.
    response = ChatResponse(
        reply=reply.reply,
        products=product_cards(DB_PATH, reply.product_ids),
        page_results=page_matches(DB_PATH, reply.page_results) if reply.page_results else None,
        cart_changed=deps.cart_changed,
    )
    if user:
        save_exchange(user.id, body.message, response, reply.page_results if response.page_results else None)
    return response


# ---------- Cart (saved to the account for logged-in shoppers) ----------


def require_user(request: Request) -> UserOut:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to save your cart to your account.")
    return user


@app.get("/api/cart", response_model=CartView)
def read_cart(request: Request) -> CartView:
    """The logged-in shopper's saved cart, priced and stock-checked right now."""
    return get_cart(DB_PATH, require_user(request).id)


@app.post("/api/cart/items", response_model=CartChange)
def add_cart_item(body: CartItemRequest, request: Request) -> CartChange:
    """Add a product + size (on top of what's already there). Sold-out sizes and over-stock amounts are refused."""
    return cart_add(DB_PATH, require_user(request).id, body.product_id, body.size, max(body.quantity, 1))


@app.patch("/api/cart/items", response_model=CartChange)
def update_cart_item(body: CartItemRequest, request: Request) -> CartChange:
    """Set a line's quantity; 0 removes it."""
    return cart_set_quantity(DB_PATH, require_user(request).id, body.product_id, body.size, body.quantity)


@app.delete("/api/cart/items/{product_id}/{size}", response_model=CartChange)
def remove_cart_item(product_id: str, size: str, request: Request) -> CartChange:
    return cart_remove(DB_PATH, require_user(request).id, product_id, size)


@app.post("/api/cart/preview", response_model=CartView)
def preview_cart(body: CartItemsRequest) -> CartView:
    """Price and stock-check a guest's browser cart (no login needed; nothing is saved)."""
    return cart_preview(DB_PATH, [(item.product_id, item.size, item.quantity) for item in body.items])


@app.post("/api/cart/merge", response_model=CartView)
def merge_cart(body: CartItemsRequest, request: Request) -> CartView:
    """Move the guest cart from the browser into the account right after logging in."""
    user = require_user(request)
    return cart_merge(DB_PATH, user.id, [(item.product_id, item.size, item.quantity) for item in body.items])


@app.patch("/api/account/preferences")
def update_preferences(body: PreferencesRequest, request: Request):
    """Turn cart reminder emails on or off for the logged-in shopper."""
    user = require_user(request)
    with db(write=True) as conn:
        conn.execute("UPDATE users SET cart_emails = ? WHERE id = ?", (int(body.cart_emails), user.id))
    return {"user": current_user(request)}


# ---------- Staff: drafted cart reminder emails ----------

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


def require_staff(request: Request) -> None:
    """Staff tools need the ADMIN_TOKEN header when one is configured; otherwise they only work on this machine."""
    token = os.getenv("ADMIN_TOKEN")
    if token:
        if request.headers.get("x-admin-token") != token:
            raise HTTPException(status_code=403, detail="Staff only.")
    elif client_ip(request) not in LOCAL_HOSTS:
        raise HTTPException(status_code=403, detail="Staff only.")


@app.get("/api/staff/outbox", response_model=list[OutboxEmail])
def outbox(request: Request) -> list[OutboxEmail]:
    """The latest drafted emails (newest first). Nothing in the outbox has been sent."""
    require_staff(request)
    return list_outbox(DB_PATH)


@app.post("/api/staff/outbox/cart-reminders", response_model=list[OutboxEmail])
async def draft_reminders(request: Request, idle_hours: float = 24) -> list[OutboxEmail]:
    """Draft reminders for opted-in shoppers whose carts have sat untouched for idle_hours (one per cart change)."""
    require_staff(request)
    return await draft_cart_reminders(DB_PATH, max(idle_hours, 0))


if __name__ == "__main__":
    # Alternative to the uvicorn command above; runs without the auto-reloader.
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
