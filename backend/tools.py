"""Tools the Campus Customs chat agent can call.

Product facts come only from data/campus_customs.db, so the agent's answers about
products, prices, and stock always come from the database rather than from the
model's memory.

Catalogue (read-only)
    search_products        find items by words, kind, color, price, or size in stock
    get_product_info       one product's description, price, colors, and sizes offered
    check_stock            live stock for one product, by size when the shopper asks

Who and where (from the per-message deps)
    get_customer_profile   the logged-in shopper's name, email, and member-since date
    get_current_page       the page the shopper is on, including the product on a product page

Cart (logged-in shoppers only)
    view_cart              their cart, with live prices and stock
    add_to_cart            add a product + size, checking stock first
    remove_from_cart       remove a product + size
    get_shopping_activity  their cart, products from recent chats, and recent searches

add_to_cart and remove_from_cart are the only tools that write anything, and they
only touch the logged-in shopper's own rows in cart_items.

Shared helpers live here too, so the agent stays four files: page_matches() re-runs
a search the agent asked to show on the page, and the "Shopping cart and cart
reminder emails" section holds the cart logic used by the tools, main.py, and agent.py.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    CartChange,
    CartLine,
    CartView,
    CurrentPage,
    CustomerProfile,
    PageContext,
    PageSearch,
    ProductCard,
    ProductInfo,
    ProductMatch,
    ProductMatches,
    ProductNotFound,
    OutboxEmail,
    ProductSummary,
    SearchResult,
    ShoppingActivity,
    SizeStock,
    StockReport,
    StockStatus,
    ViewedProduct,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# White-background photos from scripts/whiten_backgrounds.py. Their folder's timestamp goes on image URLs,
# so browsers fetch fresh copies whenever the photos are regenerated instead of showing cached ones.
WHITE_IMAGES = Path(__file__).resolve().parent.parent / "data" / "products_white"
IMAGE_VERSION = int(WHITE_IMAGES.stat().st_mtime) if WHITE_IMAGES.is_dir() else 0
LOW_STOCK = 5  # 1-5 units counts as low stock (same threshold as the product page)
MAX_RESULTS = 12  # per search_products call (keeps tool results small for the model)
PAGE_LIMIT = 60  # cards the website shows for one chat search

# How shoppers write sizes -> the catalogue's sizes.
SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "2x": "XXL", "xx-large": "XXL", "xxlarge": "XXL",
    "extra extra large": "XXL", "double xl": "XXL",
}

# The catalogue spells garment types 22 different ways; these are the kinds a shopper asks for.
# Checked in order, so "quarter-zip pullover sweatshirt" is a quarter-zip, not a sweatshirt.
GARMENT_KINDS: list[tuple[str, tuple[str, ...]]] = [
    ("quarter-zip", ("quarter-zip", "1/4 zip", "1-4 zip")),
    ("hoodie", ("hood",)),
    ("jacket", ("jacket",)),
    ("t-shirt", ("t-shirt", "t shirt", "tee")),
    ("long-sleeve", ("long-sleeve", "long sleeve")),
    ("crewneck", ("crewneck", "crew-neck", "crew neck", "mockneck", "sweatshirt")),
]

# Words a shopper uses -> words the catalogue uses.
SYNONYMS = {
    "tee": "t-shirt",
    "tees": "t-shirt",
    "tshirt": "t-shirt",
    "hoody": "hoodie",
    "quarterzip": "quarter-zip",
    "grey": "gray",
}

# Words that don't help tell products apart.
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "of", "in", "on", "with", "to", "do", "you", "have", "any",
    "anything", "something", "some", "i", "me", "my", "want", "need", "looking", "show", "find", "get",
    "is", "are", "it", "that", "this", "what", "which", "your", "got", "please", "like", "would",
    "campus", "customs", "merch", "gear", "item", "items", "one", "ones",
}


@dataclass
class ShopDeps:
    """Per-message context handed to the agent's instructions and every tool.

    main.py builds it for each chat message: the database path, the logged-in shopper (None for guests),
    and the page the shopper is on (None if the website didn't say).
    """

    db_path: Path
    customer: CustomerProfile | None = None
    page: CurrentPage | None = None
    # Set by add_to_cart / remove_from_cart so the website knows to refresh its cart badge.
    cart_changed: bool = False


# ---------- Database helpers (also used by main.py and agent.py) ----------


def _connect(db_path: Path, write: bool = False) -> sqlite3.Connection:
    """Open the shop database; read-only unless write=True (only the cart functions write)."""
    mode = "rw" if write else "ro"
    conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def image_url(image_file_path: str) -> str:
    """Public URL for a catalogue image path like 'products/x.jpg' (served by main.py)."""
    return f"/images/{image_file_path}?v={IMAGE_VERSION}" if IMAGE_VERSION else f"/images/{image_file_path}"


# Shopper-facing collections, matched on whole words in the product name. A product can be in more than one.
COLLECTIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "colleges": ("Residential Colleges", (
        "benjamin franklin", "berkeley", "branford", "davenport", "ezra stiles", "grace hopper", "jonathan edwards",
        "morse", "pauli murray", "pierson", "saybrook", "silliman", "timothy dwight", "trumbull",
    )),
    "sports": ("Sports & Teams", (
        "baseball", "basketball", "football", "hockey", "soccer", "lacrosse", "tennis", "golf", "volleyball",
        "diving", "swimming", "sailing", "squash", "fencing", "crew left chest", "track", "dry zone", "gameday",
        "tech l s",
    )),
    "family": ("Yale Family", ("mom", "dad", "grandma", "grandpa", "aunt", "uncle", "brother", "sister", "cousin")),
    "schools": ("Grad & Professional Schools", ("school of", "law school", "divinity", "forest school")),
    "classics": ("Classic Yale", (
        "vintage", "boola", "yale bowl", "arched yale", "big yale", "felt y", "shield", "harvard",
        "champion", "brooks brothers", "hype and vice", "maplehouse",
    )),
}


def product_collections(name: str) -> list[str]:
    """Collection slugs for a product, e.g. ["family"] for "Yale Dad Hoodie"."""
    text = name.lower()
    return [
        slug
        for slug, (_, words) in COLLECTIONS.items()
        if any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)
    ]


# Extra "worn on campus" photos: data/worn/<product_id>.jpg, matched from last homework's identify results.
WORN_IMAGES = Path(__file__).resolve().parent.parent / "data" / "worn"


def extra_image_urls(product_id: str) -> list[str]:
    """URLs of extra photos for a product (served by main.py at /images/worn/), or [] if there are none."""
    photo = WORN_IMAGES / f"{product_id}.jpg"
    return [f"/images/worn/{photo.name}?v={int(photo.stat().st_mtime)}"] if photo.is_file() else []


def garment_kind(garment_type: str) -> str:
    """Collapse a catalogue garment_type into one shopper-facing kind."""
    text = garment_type.lower()
    for kind, needles in GARMENT_KINDS:
        if any(needle in text for needle in needles):
            return kind
    return text


def normalise_size(size: str) -> str:
    """'medium' -> 'M', '2XL' -> 'XXL'; anything unrecognised comes back upper-cased (e.g. '3XL')."""
    key = re.sub(r"\s+", " ", size.strip().lower())
    return SIZE_ALIASES.get(key, size.strip().upper())


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "sold_out"
    if quantity <= LOW_STOCK:
        return "low_stock"
    return "in_stock"


def _size_key(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


def _stock_rows(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    sizes = [SizeStock(size=r["size"], quantity=r["quantity"], status=stock_status(r["quantity"])) for r in rows]
    return sorted(sizes, key=lambda s: _size_key(s.size))


def _sizes_in_stock_by_product(conn: sqlite3.Connection) -> dict[str, list[str]]:
    in_stock: dict[str, list[str]] = {}
    for row in conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0"):
        in_stock.setdefault(row["product_id"], []).append(row["size"])
    return {pid: sorted(sizes, key=_size_key) for pid, sizes in in_stock.items()}


def _summary(row: sqlite3.Row, sizes_in_stock: list[str]) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        description=agent_description(row),
        sizes_in_stock=sizes_in_stock,
    )


def has_real_description(description: str) -> bool:
    """Three catalogue rows hold a placeholder ("Vision blocked; filename-based stub") instead of a description."""
    return "vision blocked" not in description.lower() and "filename-based stub" not in description.lower()


def agent_description(row: sqlite3.Row) -> str:
    """The description the agent sees; empty when the catalogue has only a placeholder."""
    return row["description"] if has_real_description(row["description"]) else ""


def main_color(row: sqlite3.Row) -> str:
    """The garment's own color: the catalogue lists it first, before the print colors."""
    colors = json.loads(row["colors"])
    return colors[0].lower() if colors else ""


def _name_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _find_product(conn: sqlite3.Connection, product: str) -> sqlite3.Row | None:
    """Match a product_id exactly, or a product name ignoring case and punctuation."""
    text = product.strip()
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (text.lower(),)).fetchone()
    if row is not None:
        return row
    wanted = _name_key(text)
    for row in conn.execute("SELECT * FROM catalogue"):
        if _name_key(row["name"]) == wanted or _name_key(row["product_id"]) == wanted:
            return row
    return None


def _not_found(conn: sqlite3.Connection, product: str) -> ProductNotFound:
    rows = conn.execute("SELECT * FROM catalogue").fetchall()
    in_stock = _sizes_in_stock_by_product(conn)
    terms = _terms(product)
    scored = sorted(((_score(row, terms), row) for row in rows), key=lambda m: (-m[0], m[1]["name"]))
    suggestions = [_summary(row, in_stock.get(row["product_id"], [])) for score, row in scored[:3] if score > 0]
    return ProductNotFound(
        query=product,
        message=f"No product exactly matches '{product}'. Pick one of the suggestions or call search_products.",
        suggestions=suggestions,
    )


def product_cards(db_path: Path, product_ids: list[str]) -> list[ProductCard]:
    """Cards for the given ids, in the same order; ids that don't exist are dropped."""
    if not product_ids:
        return []
    placeholders = ",".join("?" * len(product_ids))
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            f"SELECT product_id, name, garment_type, price, image_file_path FROM catalogue "
            f"WHERE product_id IN ({placeholders})",
            product_ids,
        ).fetchall()
    by_id = {row["product_id"]: row for row in rows}
    return [
        ProductCard(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            image_url=image_url(row['image_file_path']),
        )
        for pid in dict.fromkeys(product_ids)
        if (row := by_id.get(pid)) is not None
    ]


def products_named_in(db_path: Path, text: str, limit: int = 6) -> list[str]:
    """Ids of catalogue products whose exact name appears in the text, in the order they appear."""
    lowered = text.lower()
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT product_id, name FROM catalogue").fetchall()
    found = [(lowered.find(row["name"].lower()), row["product_id"]) for row in rows]
    return [pid for pos, pid in sorted(f for f in found if f[0] >= 0)][:limit]


def unknown_product_ids(db_path: Path, product_ids: list[str]) -> list[str]:
    """Ids that aren't in the catalogue (used to stop the agent citing made-up products)."""
    known = {card.product_id for card in product_cards(db_path, product_ids)}
    return [pid for pid in product_ids if pid not in known]


# Paths the website uses, so the agent hears "the About page" rather than a raw URL.
PAGE_TYPES = {"/": "home", "/products": "products", "/about": "about", "/login": "login", "/create-account": "create-account"}


def resolve_page(db_path: Path, page: PageContext | None) -> CurrentPage | None:
    """Turn the website's page context into what the agent needs, checking the product id against the catalogue."""
    if page is None:
        return None
    path = page.path.split("?")[0].rstrip("/") or "/"
    product = None
    if page.product_id:
        with closing(_connect(db_path)) as conn:
            row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (page.product_id,)).fetchone()
        if row is not None:
            product = ViewedProduct(
                product_id=row["product_id"],
                name=row["name"],
                garment_type=row["garment_type"],
                kind=garment_kind(row["garment_type"]),
                colors=json.loads(row["colors"]),
            )
    page_type = "product" if product else PAGE_TYPES.get(path, "other")
    return CurrentPage(
        path=path,
        page_type=page_type,
        product=product,
        results_title=page.results_title if page_type == "products" else None,
    )


# ---------- Search scoring ----------


def _terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9/\-]+", text.lower())
    terms = []
    for word in words:
        if word in SYNONYMS:
            word = SYNONYMS[word]
        elif word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            word = word[:-1]  # "hoodies" -> "hoodie"; the singular still matches inside the plural
        if word not in STOPWORDS and len(word) > 1:
            terms.append(word)
    return terms


def _score(row: sqlite3.Row, terms: list[str]) -> int:
    name = row["name"].lower()
    kind = garment_kind(row["garment_type"])
    garment = row["garment_type"].lower()
    colors = " ".join(json.loads(row["colors"])).lower()
    tags = " ".join(json.loads(row["search_tags"])).lower()
    description = agent_description(row).lower()
    score = 0
    for term in terms:
        # Match at the start of a word, so "red" finds "red" but not "embroidered".
        starts_word = re.compile(rf"\b{re.escape(term)}")
        if term == "yale":  # nearly every product says Yale, so it barely helps
            score += 1 if "yale" in name else 0
            continue
        hit = 0
        if starts_word.search(name):
            hit += 4
        if term == kind or starts_word.search(garment):
            hit += 3
        if starts_word.search(tags):
            hit += 2
        if starts_word.search(colors):
            hit += 2
        if starts_word.search(description):
            hit += 1
        score += hit
    return score


def _stock_summary(name: str, sizes: list[SizeStock], requested: str | None, offered: bool) -> str:
    """One plain sentence of stock facts for the agent to rely on."""

    def label(s: SizeStock) -> str:
        return f"{s.size} (only {s.quantity} left)" if s.status == "low_stock" else s.size

    available = [label(s) for s in sizes if s.quantity > 0]
    sold_out = [s.size for s in sizes if s.quantity == 0]
    in_stock_text = f"In stock: {', '.join(available)}." if available else "It's sold out in every size right now."

    if requested and not offered:
        return f"{name} isn't made in {requested}; sizes run {SIZE_ORDER[0]}-{SIZE_ORDER[-1]}. {in_stock_text}"
    if requested:
        size = next(s for s in sizes if s.size == requested)
        if size.status == "sold_out":
            lead = f"{name} is sold out in {requested}."
        elif size.status == "low_stock":
            lead = f"{name} has only {size.quantity} left in {requested}."
        else:
            lead = f"{name} is in stock in {requested} ({size.quantity} available)."
        return f"{lead} {in_stock_text}" if size.status == "sold_out" else lead
    if not available:
        return f"{name} is sold out in every size right now."
    sold_text = f" Sold out: {', '.join(sold_out)}." if sold_out else " Every size is in stock."
    return f"{name}. {in_stock_text}{sold_text}"


# ---------- Tools ----------


def find_products(
    db_path: Path,
    query: str = "",
    kind: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> tuple[list[sqlite3.Row], list[sqlite3.Row], dict[str, list[str]]]:
    """Every catalogue row matching the filters, best match first.

    Returns (matches, rows hidden only because they're sold out in `size`, sizes in stock per product).
    Shared by the search_products tool and by page_matches, so the page shows exactly what the agent found.
    """
    terms = _terms(query)
    wanted_kind = garment_kind(SYNONYMS.get(kind.lower().strip(), kind.lower().strip())) if kind else None
    wanted_color = SYNONYMS.get(color.lower().strip(), color.lower().strip()) if color else None
    wanted_size = normalise_size(size) if size else None

    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT * FROM catalogue").fetchall()
        in_stock = _sizes_in_stock_by_product(conn)

    matches: list[tuple[int, sqlite3.Row]] = []
    hidden: list[tuple[int, sqlite3.Row]] = []  # matched, but sold out in the requested size
    for row in rows:
        if wanted_kind and garment_kind(row["garment_type"]) != wanted_kind:
            continue
        if wanted_color and wanted_color not in main_color(row):
            continue
        if max_price is not None and row["price"] > max_price:
            continue
        score = _score(row, terms) if terms else 1
        if score <= 0:
            continue
        if wanted_size and wanted_size not in in_stock.get(row["product_id"], []):
            hidden.append((score, row))
            continue
        matches.append((score, row))

    by_score = lambda m: (-m[0], m[1]["name"])  # noqa: E731
    return (
        [row for _, row in sorted(matches, key=by_score)],
        [row for _, row in sorted(hidden, key=by_score)],
        in_stock,
    )


def _short_description(description: str, limit: int = 180) -> str:
    first = re.split(r"(?<=[.!?])\s", description.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[: limit - 1].rsplit(" ", 1)[0] + "\u2026"


def page_matches(db_path: Path, page: PageSearch, limit: int = PAGE_LIMIT) -> ProductMatches | None:
    """Run the search the agent wants on the page and build its product cards; None if nothing matches."""
    f = page.filters
    rows, _, in_stock = find_products(db_path, f.query, f.kind, f.color, f.max_price, f.size)
    if not rows:
        return None
    return ProductMatches(
        title=page.title,
        filters=f,
        total_matches=len(rows),
        products=[
            ProductMatch(
                product_id=row["product_id"],
                name=row["name"],
                garment_type=row["garment_type"],
                kind=garment_kind(row["garment_type"]),
                price=row["price"],
                image_url=image_url(row['image_file_path']),
                short_description=(
                    _short_description(row["description"])
                    if has_real_description(row["description"])
                    else f"Officially licensed Yale {row['garment_type']}. The photo shows the design."
                ),
                colors=json.loads(row["colors"]),
                sizes_in_stock=in_stock.get(row["product_id"], []),
            )
            for row in rows[:limit]
        ],
        price_min=min(row["price"] for row in rows),
        price_max=max(row["price"] for row in rows),
    )


def search_products(
    ctx: RunContext[ShopDeps],
    query: str = "",
    kind: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = 8,
) -> SearchResult:
    """Search the Campus Customs catalogue. Use this before recommending or naming any product.

    Put the same filters in page_results to show every match on the website.

    Args:
        query: What the shopper is after in their words, e.g. "baseball", "Saybrook", "dad gift",
            "vintage bulldog". Leave empty to list everything that passes the filters.
        kind: Optional garment kind: "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket",
            or "long-sleeve".
        color: Optional main garment color, e.g. "navy" for navy hoodies or "gray" for gray tees
            (the color of the garment itself, not the print).
        max_price: Optional highest price in US dollars.
        size: Optional size that must be in stock right now, e.g. "XL" or "medium". For browsing only;
            to check one specific product, call check_stock instead.
        limit: How many matches to return (1-12).
    """
    matches, hidden, in_stock = find_products(ctx.deps.db_path, query, kind, color, max_price, size)
    limit = max(1, min(limit, MAX_RESULTS))
    return SearchResult(
        total_matches=len(matches),
        price_min=min((row["price"] for row in matches), default=None),
        price_max=max((row["price"] for row in matches), default=None),
        products=[_summary(row, in_stock.get(row["product_id"], [])) for row in matches[:limit]],
        sold_out_in_size=[row["name"] for row in hidden[:5]],
    )


def get_product_info(ctx: RunContext[ShopDeps], product: str) -> ProductInfo | ProductNotFound:
    """Look up one product's description, exact price, colors, and the sizes it's made in.

    Use for "tell me about…", "how much is…", or "what does it look like?" questions.
    This does not include stock; call check_stock for availability.

    Args:
        product: The product_id (best, e.g. "basic-hoodie-big-yale") or the exact product name.
    """
    with closing(_connect(ctx.deps.db_path)) as conn:
        row = _find_product(conn, product)
        if row is None:
            return _not_found(conn, product)
        sizes = _stock_rows(conn, row["product_id"])

    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        kind=garment_kind(row["garment_type"]),
        price=row["price"],
        colors=json.loads(row["colors"]),
        description=agent_description(row),
        sizes_offered=[s.size for s in sizes],
    )


def check_stock(ctx: RunContext[ShopDeps], product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Check live stock for one product, for a single size or for every size. Also returns the price.

    Call this before saying whether anything is available, sold out, or how many are left.
    Stock changes, so check again rather than relying on an earlier answer.

    Args:
        product: The product_id (best) or the exact product name.
        size: The size the shopper asked about, e.g. "M", "medium", "XL", "2XL". Leave empty for all sizes.
    """
    with closing(_connect(ctx.deps.db_path)) as conn:
        row = _find_product(conn, product)
        if row is None:
            return _not_found(conn, product)
        sizes = _stock_rows(conn, row["product_id"])

    requested_size = normalise_size(size) if size else None
    offered = requested_size is None or any(s.size == requested_size for s in sizes)
    requested = next((s for s in sizes if s.size == requested_size), None) if requested_size else None

    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        requested_size=requested_size,
        size_offered=offered,
        requested=requested,
        sizes=sizes,
        sizes_in_stock=[s.size for s in sizes if s.quantity > 0],
        total_in_stock=sum(s.quantity for s in sizes),
        summary=_stock_summary(row["name"], sizes, requested_size, offered),
    )


def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile | str:
    """Who is chatting: the logged-in shopper's name, email, when they joined, and how many messages are saved.

    Use when the shopper asks who they're logged in as, or when their name or email matters to the answer.
    """
    if ctx.deps.customer is None:
        return "The shopper is a guest (not logged in), so there's no name or email on file."
    return ctx.deps.customer


def get_current_page(ctx: RunContext[ShopDeps]) -> CurrentPage | str:
    """Which page of the website the shopper is on right now, including the product on a product page.

    Use when the shopper says "this", "it", or "this one" without naming a product.
    """
    if ctx.deps.page is None:
        return "The website didn't say which page the shopper is on."
    return ctx.deps.page


# ==================== Shopping cart and cart reminder emails ====================
# Cart logic shared by the cart tools below, by main.py (the website's cart
# endpoints and the staff outbox), and by agent.py (drafting reminder emails).
# Every price and stock number comes from catalogue/inventory at the moment it's
# read, so a cart never shows a stale price or promises stock that's gone.
#
# Tables (created by main.py at startup):
#     cart_items    one row per logged-in shopper + product + size
#     email_outbox  drafted reminder emails; nothing here is sent automatically

MAX_PER_LINE = 10  # most of one product + size a cart can hold
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:5173").rstrip("/")

CART_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id TEXT NOT NULL,
        size TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        added_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (user_id, product_id, size),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES catalogue(product_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS email_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        to_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        items_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
)


def create_cart_tables(conn: sqlite3.Connection) -> None:
    for statement in CART_TABLES:
        conn.execute(statement)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cart_items_user ON cart_items (user_id)")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "cart_emails" not in columns:
        # Opt-in for cart reminder emails; off unless the shopper turns it on.
        conn.execute("ALTER TABLE users ADD COLUMN cart_emails INTEGER NOT NULL DEFAULT 0")


# ---------- Pricing and stock-checking a list of items ----------


def _cart_line(conn: sqlite3.Connection, product_id: str, size: str, quantity: int) -> CartLine:
    product = conn.execute(
        "SELECT name, price, image_file_path FROM catalogue WHERE product_id = ?", (product_id,)
    ).fetchone()
    stock = conn.execute(
        "SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (product_id, size)
    ).fetchone()
    if product is None or stock is None:
        return CartLine(
            product_id=product_id, name=product["name"] if product else product_id, size=size,
            quantity=quantity, price=0, line_total=0, image_url=image_url(product["image_file_path"]) if product else "",
            in_stock=0, status="unavailable", note="This item is no longer available.",
        )
    in_stock = stock["quantity"]
    if in_stock == 0:
        status, note = "sold_out", f"Sold out in {size} right now."
    elif quantity > in_stock:
        status, note = "exceeds_stock", f"Only {in_stock} left in {size}."
    elif in_stock <= LOW_STOCK:
        status, note = "low_stock", f"Only {in_stock} left in {size}."
    else:
        status, note = "ok", ""
    return CartLine(
        product_id=product_id, name=product["name"], size=size, quantity=quantity,
        price=product["price"], line_total=round(product["price"] * quantity, 2),
        image_url=image_url(product["image_file_path"]), in_stock=in_stock, status=status, note=note,
    )


def _cart_view(lines: list[CartLine]) -> CartView:
    lines = sorted(lines, key=lambda line: (line.name, _size_key(line.size)))
    buyable = [line for line in lines if line.status not in ("sold_out", "unavailable")]
    return CartView(
        lines=lines,
        item_count=sum(line.quantity for line in lines),
        subtotal=round(sum(line.line_total for line in buyable), 2),
        has_problems=any(line.status in ("sold_out", "exceeds_stock", "unavailable") for line in lines),
    )


def cart_preview(db_path: Path, items: list[tuple[str, str, int]]) -> CartView:
    """Price a guest's browser cart. Quantities are capped at stock and MAX_PER_LINE; duplicates are combined."""
    combined: dict[tuple[str, str], int] = {}
    for product_id, size, quantity in items:
        if quantity > 0:
            key = (product_id, normalise_size(size))
            combined[key] = min(combined.get(key, 0) + quantity, MAX_PER_LINE)
    with closing(_connect(db_path)) as conn:
        lines = []
        for (product_id, size), quantity in combined.items():
            line = _cart_line(conn, product_id, size, quantity)
            if line.status == "exceeds_stock":
                line = _cart_line(conn, product_id, size, line.in_stock)
            lines.append(line)
    return _cart_view(lines)


# ---------- A logged-in shopper's saved cart ----------


def get_cart(db_path: Path, user_id: int) -> CartView:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT product_id, size, quantity FROM cart_items WHERE user_id = ?", (user_id,)
        ).fetchall()
        return _cart_view([_cart_line(conn, r["product_id"], r["size"], r["quantity"]) for r in rows])


def cart_add(db_path: Path, user_id: int, product_id: str, size: str, quantity: int = 1) -> CartChange:
    """Add to the cart (on top of anything already there), never beyond stock or MAX_PER_LINE."""
    size = normalise_size(size)
    ok, message = False, ""
    with closing(_connect(db_path, write=True)) as conn, conn:
        product = conn.execute("SELECT name FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        stock = conn.execute(
            "SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (product_id, size)
        ).fetchone()
        existing = conn.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ? AND size = ?",
            (user_id, product_id, size),
        ).fetchone()
        current = existing["quantity"] if existing else 0

        if product is None:
            message = "That product isn't in the catalogue."
        elif stock is None:
            message = f"{product['name']} isn't made in {size}. Sizes run XS to XXL."
        elif stock["quantity"] == 0:
            message = f"{product['name']} is sold out in {size} right now, so it wasn't added."
        else:
            wanted = current + max(quantity, 1)
            allowed = min(wanted, stock["quantity"], MAX_PER_LINE)
            if allowed <= current:
                limit = min(stock["quantity"], MAX_PER_LINE)
                message = f"Your cart already has {current} of {product['name']} in {size}, the most available ({limit})."
            else:
                conn.execute(
                    """
                    INSERT INTO cart_items (user_id, product_id, size, quantity) VALUES (?, ?, ?, ?)
                    ON CONFLICT (user_id, product_id, size)
                    DO UPDATE SET quantity = excluded.quantity, updated_at = datetime('now')
                    """,
                    (user_id, product_id, size, allowed),
                )
                ok = True
                added = allowed - current
                what = f"{product['name']} ({size})" if added == 1 else f"{added} of {product['name']} ({size})"
                message = f"Added {what} to the cart."
                if allowed < wanted:
                    message += f" That's the most available right now ({allowed} in the cart)."
    return CartChange(ok=ok, message=message, cart=get_cart(db_path, user_id))


def cart_set_quantity(db_path: Path, user_id: int, product_id: str, size: str, quantity: int) -> CartChange:
    """Set a line's quantity (0 removes it), capped at stock and MAX_PER_LINE."""
    size = normalise_size(size)
    if quantity <= 0:
        return cart_remove(db_path, user_id, product_id, size)
    with closing(_connect(db_path, write=True)) as conn, conn:
        stock = conn.execute(
            "SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (product_id, size)
        ).fetchone()
        allowed = min(quantity, MAX_PER_LINE, stock["quantity"] if stock else 0)
        if allowed <= 0:
            changed = conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ? AND size = ?", (user_id, product_id, size)
            ).rowcount
        else:
            changed = conn.execute(
                "UPDATE cart_items SET quantity = ?, updated_at = datetime('now') "
                "WHERE user_id = ? AND product_id = ? AND size = ?",
                (allowed, user_id, product_id, size),
            ).rowcount
    if not changed:
        ok, message = False, "That item isn't in your cart."
    elif allowed <= 0:
        ok, message = False, f"That item is sold out in {size}, so it was removed."
    elif allowed < quantity:
        ok, message = True, f"Only {allowed} available, so that's what's in your cart."
    else:
        ok, message = True, "Updated your cart."
    return CartChange(ok=ok, message=message, cart=get_cart(db_path, user_id))


def cart_remove(db_path: Path, user_id: int, product_id: str, size: str) -> CartChange:
    size = normalise_size(size)
    with closing(_connect(db_path, write=True)) as conn, conn:
        removed = conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ? AND size = ?", (user_id, product_id, size)
        ).rowcount
    message = "Removed it from your cart." if removed else "That item wasn't in your cart."
    return CartChange(ok=bool(removed), message=message, cart=get_cart(db_path, user_id))


def cart_merge(db_path: Path, user_id: int, items: list[tuple[str, str, int]]) -> CartView:
    """Move a guest's browser cart into their account at login (adding to what's already saved)."""
    for product_id, size, quantity in items:
        if quantity > 0:
            cart_add(db_path, user_id, product_id, size, quantity)
    return get_cart(db_path, user_id)


# ---------- Abandoned carts and reminder emails ----------


@dataclass
class IdleCart:
    user_id: int
    first_name: str
    email: str
    cart: CartView


def idle_carts(db_path: Path, idle_hours: float) -> list[IdleCart]:
    """Opted-in shoppers whose cart hasn't changed in `idle_hours` and who haven't had a reminder since."""
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT users.id, users.name, users.first_name, users.email, MAX(cart_items.updated_at) AS last_change
            FROM cart_items JOIN users ON users.id = cart_items.user_id
            WHERE users.cart_emails = 1
            GROUP BY users.id
            HAVING last_change <= datetime('now', ?)
               AND NOT EXISTS (
                   SELECT 1 FROM email_outbox
                   WHERE email_outbox.user_id = users.id AND email_outbox.kind = 'abandoned_cart'
                     AND email_outbox.created_at >= last_change
               )
            """,
            (f"-{max(idle_hours, 0)} hours",),
        ).fetchall()
    carts = []
    for row in rows:
        cart = get_cart(db_path, row["id"])
        if any(line.status not in ("sold_out", "unavailable") for line in cart.lines):
            first = row["first_name"] or row["name"].split(" ")[0]
            carts.append(IdleCart(user_id=row["id"], first_name=first, email=row["email"], cart=cart))
    return carts


def cart_facts(cart: CartView) -> str:
    """The cart as plain facts, given to the model so its friendly words match what's really in the cart."""
    lines = []
    for line in cart.lines:
        stock = {"low_stock": f"only {line.in_stock} left", "exceeds_stock": f"only {line.in_stock} left",
                 "sold_out": "now sold out", "unavailable": "no longer sold"}.get(line.status, "in stock")
        lines.append(f"- {line.name}, size {line.size}, quantity {line.quantity} ({stock})")
    return "\n".join(lines)


def render_cart_email(first_name: str, cart: CartView, subject: str, opening: str, closing_line: str) -> tuple[str, str]:
    """Build the full email: the model's friendly words around items, prices, and links filled in by code."""
    items = []
    for line in cart.lines:
        detail = f"- {line.name} (size {line.size}) x{line.quantity}: ${line.line_total:,.2f}"
        if line.status in ("sold_out", "unavailable"):
            detail = f"- {line.name} (size {line.size}): {line.note}"
        elif line.note:
            detail += f". {line.note}"
        items.append(detail)
    body = "\n".join(
        [
            f"Hi {first_name},",
            "",
            opening.strip(),
            "",
            "Still in your cart:",
            *items,
            "",
            f"Subtotal: ${cart.subtotal:,.2f} (prices and stock as of this email)",
            "",
            f"Pick up where you left off: {SITE_URL}/cart",
            "",
            closing_line.strip(),
            "",
            "Campus Customs",
            "57 Broadway, New Haven, CT 06511 · orderdept@campuscustoms.com · (475) 301-4205",
            "",
            "You're getting this because you asked for cart reminders. You can turn them off on your cart page.",
        ]
    )
    return subject.strip(), body


def fallback_email_copy(first_name: str) -> tuple[str, str, str]:
    """Plain wording used if the model can't be reached, so a reminder can still be drafted."""
    return (
        "You left some Yale gear in your cart",
        "Just a heads-up: the things you picked out are still waiting in your cart.",
        "Questions about sizing? Reply here or ask the chat on our site.",
    )


def save_email_draft(db_path: Path, idle: IdleCart, subject: str, body: str) -> OutboxEmail:
    items = [{"product_id": l.product_id, "size": l.size, "quantity": l.quantity, "price": l.price} for l in idle.cart.lines]
    with closing(_connect(db_path, write=True)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO email_outbox (user_id, kind, to_email, subject, body, items_json) VALUES (?, 'abandoned_cart', ?, ?, ?, ?)",
            (idle.user_id, idle.email, subject, body, json.dumps(items)),
        )
        row = conn.execute("SELECT * FROM email_outbox WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _outbox_email(row)


def list_outbox(db_path: Path, limit: int = 50) -> list[OutboxEmail]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT * FROM email_outbox ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_outbox_email(row) for row in rows]


def _outbox_email(row: sqlite3.Row) -> OutboxEmail:
    return OutboxEmail(
        id=row["id"], user_id=row["user_id"], kind=row["kind"], to_email=row["to_email"],
        subject=row["subject"], body=row["body"], status=row["status"], created_at=row["created_at"],
    )


# ---------- Cart tools (logged-in shoppers only) ----------

GUEST_CART = (
    "The shopper is a guest, so you can't see or change their cart from the chat. Tell them to use the "
    "Add to cart button on the product page, or to log in so you can help with their cart."
)


def view_cart(ctx: RunContext[ShopDeps]) -> CartView | str:
    """See what's in the logged-in shopper's cart, with current prices, stock for each size, and the subtotal.

    Use for "what's in my cart?", "is everything in my cart still in stock?", or "how much is my cart?".
    """
    if ctx.deps.customer is None:
        return GUEST_CART
    return get_cart(ctx.deps.db_path, ctx.deps.customer.user_id)


def add_to_cart(
    ctx: RunContext[ShopDeps], product: str, size: str, quantity: int = 1
) -> CartChange | ProductNotFound | str:
    """Add a product in one size to the logged-in shopper's cart. Checks live stock; never adds a sold-out size.

    Only call this when the shopper clearly asks to add something and you know the exact product and size.
    If they haven't said a size, ask first instead of guessing.

    Args:
        product: The product_id (best) or exact product name.
        size: XS, S, M, L, XL, or XXL ("medium", "2XL", etc. are understood).
        quantity: How many to add (1-10).
    """
    if ctx.deps.customer is None:
        return GUEST_CART
    with closing(_connect(ctx.deps.db_path)) as conn:
        row = _find_product(conn, product)
        if row is None:
            return _not_found(conn, product)
    change = cart_add(ctx.deps.db_path, ctx.deps.customer.user_id, row["product_id"], size, max(1, min(quantity, 10)))
    ctx.deps.cart_changed = ctx.deps.cart_changed or change.ok
    return change


def remove_from_cart(ctx: RunContext[ShopDeps], product: str, size: str) -> CartChange | ProductNotFound | str:
    """Remove a product in one size from the logged-in shopper's cart, when they ask to.

    Args:
        product: The product_id (best) or exact product name.
        size: The size of the cart line to remove.
    """
    if ctx.deps.customer is None:
        return GUEST_CART
    with closing(_connect(ctx.deps.db_path)) as conn:
        row = _find_product(conn, product)
        if row is None:
            return _not_found(conn, product)
    change = cart_remove(ctx.deps.db_path, ctx.deps.customer.user_id, row["product_id"], size)
    ctx.deps.cart_changed = ctx.deps.cart_changed or change.ok
    return change


def get_shopping_activity(ctx: RunContext[ShopDeps]) -> ShoppingActivity | str:
    """What the logged-in shopper has been looking at: their cart, products from their recent chats, and recent
    searches. Use it to make personal suggestions ("you were looking at quarter-zips...") or when they ask
    what they looked at before.
    """
    if ctx.deps.customer is None:
        return "The shopper is a guest, so there's no saved activity. Just help with what they ask."
    user_id = ctx.deps.customer.user_id
    with closing(_connect(ctx.deps.db_path)) as conn:
        rows = conn.execute(
            "SELECT products_json, page_json FROM chat_messages "
            "WHERE user_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 30",
            (user_id,),
        ).fetchall()
    discussed: list[str] = []
    searches: list[str] = []
    for row in rows:
        for item in json.loads(row["products_json"] or "[]"):
            if isinstance(item, dict) and item.get("product_id") and item["product_id"] not in discussed:
                discussed.append(item["product_id"])
        if row["page_json"]:
            title = json.loads(row["page_json"]).get("title")
            if title and title not in searches:
                searches.append(title)
    return ShoppingActivity(
        cart=get_cart(ctx.deps.db_path, user_id),
        recently_discussed=product_cards(ctx.deps.db_path, discussed[:8]),
        recent_searches=searches[:5],
    )


TOOLS = [
    search_products,
    get_product_info,
    check_stock,
    get_customer_profile,
    get_current_page,
    view_cart,
    add_to_cart,
    remove_from_cart,
    get_shopping_activity,
]
# Tools whose results contain prices or stock (agent.py checks one ran before a reply quotes either).
FACT_TOOLS = {
    "search_products", "get_product_info", "check_stock",
    "view_cart", "add_to_cart", "remove_from_cart", "get_shopping_activity",
}
