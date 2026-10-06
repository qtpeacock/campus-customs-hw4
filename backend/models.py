"""Pydantic / PydanticAI structured types for the Campus Customs backend.

Grouped by where they're used: product data the tools return, the chat
request/response that crosses the API, the agent's structured output, and the
account forms.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ---------- Products (returned by tools, shown as cards) ----------

StockStatus = Literal["in_stock", "low_stock", "sold_out"]
COLORS_DESCRIPTION = (
    "Every color that appears on this one item (garment color first, then the print). "
    "These are not separate color options; each product comes in a single colorway."
)


class SizeStock(BaseModel):
    """Live stock for one size of one product."""

    size: str = Field(description="One of XS, S, M, L, XL, XXL.")
    quantity: int = Field(description="Units in stock right now; 0 means sold out in this size.")
    status: StockStatus = Field(description="sold_out at 0, low_stock at 1-5, in_stock above 5.")


class ProductSummary(BaseModel):
    """One search_products match: enough to recommend an item honestly without another call."""

    product_id: str = Field(description="Stable id to pass to get_product_info / check_stock and to list for cards.")
    name: str
    garment_type: str = Field(description="The catalogue's own wording, e.g. 'pullover hoodie'.")
    price: float = Field(description="Exact price in US dollars, straight from the catalogue.")
    colors: list[str] = Field(description=COLORS_DESCRIPTION)
    description: str = Field(
        description="How the item looks. Empty when the catalogue has no description yet; then don't describe its look."
    )
    sizes_in_stock: list[str] = Field(
        description="Sizes with at least one unit right now, XS to XXL. Use check_stock for exact quantities."
    )


class SearchResult(BaseModel):
    total_matches: int = Field(description="How many catalogue items matched before the limit was applied.")
    price_min: float | None = Field(description="Lowest price across ALL matches, not just the ones listed.")
    price_max: float | None = Field(description="Highest price across ALL matches, not just the ones listed.")
    products: list[ProductSummary] = Field(description="The best matches, up to the limit; may be only some of them.")
    sold_out_in_size: list[str] = Field(
        default_factory=list,
        description=(
            "When a size filter was used: names of items that matched everything else but are sold out "
            "in that size, so they were left out of products. Mention these if the shopper asked about one."
        ),
    )


class ProductInfo(BaseModel):
    """get_product_info: the full catalogue entry for one product (no stock; use check_stock for that)."""

    product_id: str
    name: str
    garment_type: str
    kind: str = Field(description="Shopper-facing kind: hoodie, crewneck, t-shirt, quarter-zip, jacket, or long-sleeve.")
    price: float = Field(description="Exact price in US dollars, straight from the catalogue.")
    colors: list[str] = Field(description=COLORS_DESCRIPTION)
    description: str = Field(
        description=(
            "The catalogue's full description of how the item looks. Empty when there isn't one yet; "
            "then say so and suggest the photo on its product page."
        )
    )
    sizes_offered: list[str] = Field(description="Every size this product is made in, whether or not it's in stock now.")


class StockReport(BaseModel):
    """check_stock: live stock for one product, focused on the size the shopper asked about."""

    product_id: str
    name: str
    price: float = Field(description="Exact price in US dollars, so price-and-stock questions need only this call.")
    requested_size: str | None = Field(
        description="The size asked about, normalised (e.g. 'medium' -> 'M'); null when no size was asked."
    )
    size_offered: bool = Field(
        description="False when the requested size isn't one we make (e.g. 3XL); then requested is null."
    )
    requested: SizeStock | None = Field(description="Stock for the requested size, if one was asked and is offered.")
    sizes: list[SizeStock] = Field(description="Stock for every size, XS to XXL.")
    sizes_in_stock: list[str]
    total_in_stock: int = Field(description="Units across all sizes.")
    summary: str = Field(description="One plain sentence stating the stock facts; safe to repeat to the shopper.")


class ProductNotFound(BaseModel):
    """Returned instead of ProductInfo / StockReport when the product can't be matched exactly."""

    query: str
    message: str
    suggestions: list[ProductSummary] = Field(description="Closest catalogue matches, so the agent can pick or ask.")


class ProductCard(BaseModel):
    """A product card the website shows under a chat reply. Built from the database, never by the model."""

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str


# ---------- Chat search on the page (agent -> API -> website) ----------


class CatalogueFilters(BaseModel):
    """The same filters search_products takes; the backend re-runs them to fill the page."""

    query: str = Field(default="", max_length=100, description="Shopper's words, e.g. 'baseball', 'Saybrook', 'dad'.")
    kind: str | None = Field(
        default=None, description="hoodie, crewneck, t-shirt, quarter-zip, jacket, or long-sleeve."
    )
    color: str | None = Field(
        default=None, description="Main garment color, e.g. 'navy' for navy hoodies (not the print color)."
    )
    max_price: float | None = Field(default=None, description="Highest price in US dollars.")
    size: str | None = Field(default=None, description="A size that must be in stock right now, e.g. 'XL'.")


class PageSearch(BaseModel):
    """Part of the agent's output: which catalogue search should fill the page with product cards."""

    title: str = Field(
        max_length=60,
        description="Short heading for the results, e.g. 'Hoodies', 'Saybrook College', 'Gifts for Dad under $60'.",
    )
    filters: CatalogueFilters = Field(description="The filters that found these items with search_products.")


class ProductMatch(BaseModel):
    """One product card on the page: image, name, price, and short info. Built from the database."""

    product_id: str
    name: str
    garment_type: str
    kind: str
    price: float
    image_url: str
    short_description: str = Field(description="The first sentence of the catalogue description, trimmed.")
    colors: list[str]
    sizes_in_stock: list[str]


class ProductMatches(BaseModel):
    """What the API sends the website when a chat search should update the page."""

    title: str
    filters: CatalogueFilters
    total_matches: int = Field(description="Everything that matched, even beyond what's shown.")
    products: list[ProductMatch] = Field(description="Matches in relevance order, up to the page limit.")
    price_min: float
    price_max: float


# ---------- Chat over the API ----------


class ChatTurn(BaseModel):
    """One earlier message in the conversation, as the browser remembers it."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Products shown as cards with an assistant reply, so follow-ups like 'the first one' make sense.",
    )
    page_title: str | None = Field(
        default=None,
        max_length=60,
        description="Title of the chat results this reply put on the page, so 'which of those…' follow-ups make sense.",
    )


class PageContext(BaseModel):
    """Sent by the website with every chat message: where the shopper is right now."""

    path: str = Field(default="/", max_length=200, description="The page's path, e.g. '/products/basic-hoodie-big-yale'.")
    product_id: str | None = Field(default=None, max_length=100, description="Set when the shopper is on a product page.")
    results_title: str | None = Field(
        default=None, max_length=60, description="Title of the chat results showing on the Products page, if any."
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=40,
        description="Guests only: the browser's recent turns. Logged-in shoppers' history comes from the database.",
    )
    page: PageContext | None = None

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Type a message first.")
        return value


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list, description="A few cards shown inside the chat.")
    page_results: ProductMatches | None = Field(
        default=None, description="When set, the website shows these matches on the page as product cards."
    )
    cart_changed: bool = Field(default=False, description="True when the agent added to or removed from the cart.")


class StoredChatMessage(BaseModel):
    """One saved message, as GET /api/chat/history returns it."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list, description="Chat cards, rebuilt from the database.")
    page_results: ProductMatches | None = Field(default=None, description="Page results that reply showed, re-run.")
    created_at: str


class ChatHistory(BaseModel):
    logged_in: bool
    messages: list[StoredChatMessage]


# ---------- Who is chatting, and what page they're on (agent deps) ----------


class CustomerProfile(BaseModel):
    """The logged-in shopper as the agent sees them. No password hash, session, or other shoppers' data."""

    user_id: int
    first_name: str
    last_name: str
    name: str
    email: str
    member_since: str = Field(description="Date the account was created, YYYY-MM-DD.")
    saved_messages: int = Field(description="How many earlier chat messages are saved for this shopper.")


class ViewedProduct(BaseModel):
    """The product on the page the shopper is looking at."""

    product_id: str
    name: str
    garment_type: str
    kind: str
    colors: list[str] = Field(description=COLORS_DESCRIPTION)


class CurrentPage(BaseModel):
    """What the agent knows about the shopper's current page (built by the backend from PageContext)."""

    path: str
    page_type: Literal["home", "products", "product", "about", "login", "create-account", "other"]
    product: ViewedProduct | None = Field(
        default=None, description="Set on a product page; 'this' or 'it' in the shopper's message means this item."
    )
    results_title: str | None = Field(default=None, description="Chat results showing on the Products page, if any.")


# ---------- Shopping cart and cart reminder emails ----------

CartLineStatus = Literal["ok", "low_stock", "exceeds_stock", "sold_out", "unavailable"]


class CartLine(BaseModel):
    """One product + size in a cart, priced and stock-checked live from the database."""

    product_id: str
    name: str
    size: str
    quantity: int
    price: float = Field(description="Current catalogue price for one item.")
    line_total: float
    image_url: str
    in_stock: int = Field(description="Units of this size in stock right now.")
    status: CartLineStatus = Field(
        description=(
            "ok; low_stock (5 or fewer left); exceeds_stock (cart wants more than are left); "
            "sold_out (none left in this size); unavailable (product or size no longer sold)."
        )
    )
    note: str = Field(default="", description="A short plain-English note about stock, empty when all is well.")


class CartView(BaseModel):
    lines: list[CartLine]
    item_count: int = Field(description="Total units across all lines.")
    subtotal: float = Field(description="Sum of line totals, at current prices.")
    has_problems: bool = Field(description="True if any line is sold out, over the stock limit, or unavailable.")


class CartChange(BaseModel):
    """The result of adding, changing, or removing a cart item."""

    ok: bool
    message: str = Field(description="Plain-English result, e.g. 'Added Yale Dad Hoodie (M) to the cart.'")
    cart: CartView


class CartItemRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    size: str = Field(min_length=1, max_length=10)
    quantity: int = Field(default=1, ge=0, le=10)


class CartItemsRequest(BaseModel):
    """A guest's browser cart, sent to be priced (preview) or moved into their account at login (merge)."""

    items: list[CartItemRequest] = Field(default_factory=list, max_length=50)


class PreferencesRequest(BaseModel):
    cart_emails: bool = Field(description="Whether the shopper wants a reminder email about items left in their cart.")


class CartEmailCopy(BaseModel):
    """The model writes only the friendly words of a cart reminder; the code adds items, prices, and links."""

    subject: str = Field(max_length=70, description="Short, friendly subject line with no prices or numbers.")
    opening: str = Field(max_length=300, description="One or two sentences after the greeting. No prices or stock numbers.")
    closing: str = Field(max_length=200, description="One short sign-off sentence. No prices or stock numbers.")


class OutboxEmail(BaseModel):
    """A drafted email waiting in email_outbox. Nothing is sent automatically."""

    id: int
    user_id: int
    kind: str
    to_email: str
    subject: str
    body: str
    status: str
    created_at: str


class ShoppingActivity(BaseModel):
    """get_shopping_activity: what the logged-in shopper has been looking at, for helpful suggestions."""

    cart: CartView
    recently_discussed: list[ProductCard] = Field(
        description="Products shown in this shopper's recent chats (newest first), with current prices."
    )
    recent_searches: list[str] = Field(description="Titles of recent chat searches put on the Products page.")


# ---------- Audit trail (output/audit_trail.json) ----------

AuditEvent = Literal["run_start", "model_request", "tool_call", "tool_result", "retry", "run_end"]


class AuditEntry(BaseModel):
    """One step of agent-loop activity. Entries are only ever appended to output/audit_trail.json."""

    timestamp: str = Field(description="When it happened, ISO 8601 in UTC.")
    run_id: str = Field(description="Groups every entry from one agent run, e.g. 'chat-20261006T021500-3fa2c1'.")
    kind: Literal["chat", "cart_email"] = Field(description="Which agent ran: the shop chat or the reminder email writer.")
    event: AuditEvent
    step: int | None = Field(default=None, description="Model round-trip number within the run (1, 2, …).")
    tool_name: str | None = None
    tool_args: str = Field(default="", description="Short, redacted JSON of the tool's arguments.")
    tool_result: str = Field(default="", description="Short, redacted summary of what the tool or retry returned.")
    stop_reason: str | None = Field(
        default=None,
        description="Only on run_end: final_result, content_filter, usage_limit, not_configured, or error: <type>.",
    )
    detail: dict = Field(
        default_factory=dict,
        description="run_start: shopper, page, message preview, model. run_end: duration, usage, output summary.",
    )


# ---------- Agent output ----------


class ChatReply(BaseModel):
    """The agent's structured answer to one shopper message."""

    reply: str = Field(description="The message to show the shopper, in plain text (no markdown).")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "product_id values of the items the reply recommends or talks about, in the order mentioned, "
            "so the website can show them as cards. Only ids returned by a tool in this conversation; "
            "empty when no specific product is relevant."
        ),
    )
    page_results: PageSearch | None = Field(
        default=None,
        description=(
            "Set when the shopper is browsing a type or group of items (e.g. 'what hoodies do you have', "
            "'show me Saybrook stuff', 'gifts under $50'), so the website shows every match on the page. "
            "Null for questions about one specific product, stock, sizes, or policies."
        ),
    )


# ---------- Accounts ----------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    cart_emails: bool = Field(default=False, description="Opted in to cart reminder emails at sign-up.")

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter your name.")
        return value

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    """The public view of a shopper. There is deliberately no password field."""

    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    cart_emails: bool = False
