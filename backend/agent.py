"""Campus Customs chat agent: entry point and wiring.

Builds a PydanticAI agent whose instructions are prompts/prompt.md, whose model
is reached through Portkey's OpenAI-compatible endpoint, and whose tools come
from tools.py. main.py calls run_chat() for every message from the website.

Try it from a terminal (run from backend/):
    python agent.py "do you have any hoodies under $70?"
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits  # noqa: E402
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402

from models import AuditEntry, CartEmailCopy, CartView, ChatReply, ChatTurn, OutboxEmail  # noqa: E402
from tools import (  # noqa: E402
    FACT_TOOLS,
    TOOLS,
    ShopDeps,
    cart_facts,
    fallback_email_copy,
    find_products,
    idle_carts,
    products_named_in,
    render_cart_email,
    save_email_draft,
    unknown_product_ids,
)

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
DB_PATH = HERE.parent / "data" / "campus_customs.db"

# HW4/.env first if it exists, then the course-wide .env one level up (where PORTKEY_API_KEY lives).
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE.parent.parent / ".env")

DEFAULT_MODEL = "gpt-5.6-luna"
HISTORY_TURNS = 12  # how many earlier messages travel with each new one
USAGE_LIMITS = UsageLimits(request_limit=8)  # caps model round-trips per message

# A reply that quotes a price or a stock level ("$58", "sold out", "only 3 left", "12 available").
PRICE_OR_STOCK = re.compile(
    r"\$\s?\d|\bin stock\b|\bsold out\b|\bout of stock\b|\b\d+\s+(?:left|available|in stock)\b",
    re.IGNORECASE,
)

# Sent when the model provider's content filter blocks a message (e.g. a jailbreak attempt).
FILTERED_REPLY = (
    "I can't help with that one, but I'm happy to help you find some Yale gear, "
    "check sizes and stock, or explain shipping and returns."
)


class AgentNotConfigured(RuntimeError):
    """PORTKEY_API_KEY is missing, so main.py can answer with a clear 503 instead of crashing."""


def model_name() -> str:
    """CHAT_MODEL wins if set, then OPENAI_MODEL from .env, then gpt-5.6-luna."""
    return os.getenv("CHAT_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL


def _safe_name(name: str | None, limit: int = 30) -> str:
    """Shoppers choose their own name, so keep only name-like characters before it reaches the prompt."""
    return re.sub(r"[^A-Za-zÀ-ÿ' \-]", "", name or "").strip()[:limit]


def _safe_email(email: str) -> str:
    return re.sub(r"[^A-Za-z0-9@._+\-]", "", email)[:100]


def shopper_and_page_context(deps: ShopDeps) -> str:
    """The "right now" block added to the instructions on every message: who is chatting and what page they're on."""
    lines = ["## Right now"]

    customer = deps.customer
    if customer:
        first = _safe_name(customer.first_name) or "there"
        full = _safe_name(customer.name, 60) or first
        lines.append(
            f'- Shopper: logged in as "{full}" (first name "{first}", email {_safe_email(customer.email)}), '
            f"a member since {customer.member_since}. Their chat history is saved, so earlier messages in this "
            "conversation may be from a previous visit. Use their first name now and then. Only mention their "
            "email if they ask which account they're using."
        )
    else:
        lines.append("- Shopper: a guest (not logged in). You don't know their name or email; don't ask for them.")

    page = deps.page
    if page is None:
        lines.append("- Page: unknown.")
    elif page.product:
        product = page.product
        colors = ", ".join(product.colors) or "not listed"
        lines.append(
            f'- Page: the product page for "{product.name}" (product_id {product.product_id}; {product.garment_type}; '
            f"colors on this item: {colors}). When the shopper says \"this\", \"it\", or \"this one\" without naming "
            "a product, they mean this item: use its product_id with check_stock or get_product_info, and list it "
            "in product_ids."
        )
    elif page.page_type == "products" and page.results_title:
        lines.append(f'- Page: the Products page, showing your earlier "{page.results_title}" results.')
    elif page.page_type == "products":
        lines.append("- Page: the Products page, showing the full catalogue.")
    else:
        lines.append(f"- Page: the {page.page_type.replace('-', ' ')} page ({page.path}).")
    return "\n".join(lines)


def _build_model() -> OpenAIChatModel:
    """The chat model, reached through Portkey's OpenAI-compatible endpoint with PORTKEY_API_KEY."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers={"x-portkey-api-key": api_key},
        timeout=60,
    )
    return OpenAIChatModel(model_name(), provider=OpenAIProvider(openai_client=client))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, ChatReply]:
    """Create the agent once, on the first chat message."""
    model = _build_model()
    agent = Agent(
        model,
        deps_type=ShopDeps,
        output_type=ChatReply,
        tools=TOOLS,
        retries=2,
    )

    @agent.instructions
    def system_prompt() -> str:
        # Read on every message, so edits to prompt.md apply without restarting the server.
        return PROMPT_PATH.read_text(encoding="utf-8")

    @agent.instructions
    def right_now(ctx: RunContext[ShopDeps]) -> str:
        # Who is chatting and which page they're on, from the deps main.py built for this message.
        return shopper_and_page_context(ctx.deps)

    @agent.output_validator
    def grounded_in_database(ctx: RunContext[ShopDeps], output: ChatReply) -> ChatReply:
        unknown = unknown_product_ids(ctx.deps.db_path, output.product_ids)
        if unknown:
            raise ModelRetry(
                f"These product_ids are not in the catalogue: {unknown}. "
                "Only use ids returned by search_products, get_product_info, or check_stock."
            )
        # History holds only text, so any tool call in ctx.messages happened during this message.
        if PRICE_OR_STOCK.search(output.reply) and not (_tools_called(ctx.messages) & FACT_TOOLS):
            raise ModelRetry(
                "Your reply states a price or stock level, but you haven't looked it up for this message. "
                "Call check_stock (stock and price), get_product_info (price and description), or "
                "search_products first, and use exactly what they return."
            )
        if output.page_results is not None:
            f = output.page_results.filters
            matches, _, _ = find_products(ctx.deps.db_path, f.query, f.kind, f.color, f.max_price, f.size)
            if not matches:
                raise ModelRetry(
                    f"page_results filters {f.model_dump(exclude_defaults=True)} match no products. "
                    "Use the filters from a search_products call that returned items, or set page_results to null."
                )
        return output

    return agent


# ---------- Audit trail (output/audit_trail.json) ----------
# Append-only audit trail of agent-loop activity: output/audit_trail.json.
#
# Every chat message and every cart-reminder email is one agent run. As the run
# goes, this records a run_start, each model request, each tool call and its
# result, any retry (a tool or the output validator sending the model back), and
# a run_end with the stop reason, timing, and token usage.
#
# Entries are appended one at a time while the run is still going, so a run
# that crashes still leaves its history. The file is never wiped: existing
# entries are always read back and kept, and if the file is ever unreadable it
# is moved aside (audit_trail.corrupt-<time>.json) rather than overwritten.
#
# Arguments and results are shortened and redacted (emails and long digit
# strings like card numbers are masked) so the trail never holds a full payload
# or sensitive details.

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
ARGS_CHARS = 200
RESULT_CHARS = 240
MESSAGE_CHARS = 120

_LOCK = asyncio.Lock()
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
LONG_NUMBER = re.compile(r"\b(?:\d[ -]?){12,19}\b")


def redact(text: str) -> str:
    """Mask emails and card-like numbers."""
    return LONG_NUMBER.sub("[number]", EMAIL.sub("[email]", text))


def short(value: Any, limit: int) -> str:
    """A one-line, redacted, length-capped version of any value."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = redact(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class AuditTrail:
    """Writes the entries for one agent run."""

    def __init__(self, kind: str, path: Path = AUDIT_PATH) -> None:
        self.kind = kind
        self.path = path
        self.run_id = f"{kind}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid4().hex[:6]}"
        self.step = 0
        self.started = time.perf_counter()

    async def append(self, event: str, **fields: Any) -> None:
        entry = AuditEntry(timestamp=_now(), run_id=self.run_id, kind=self.kind, event=event, **fields)
        async with _LOCK:
            entries = self._read()
            entries.append(entry.model_dump())
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".json.tmp")
            temp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(temp, self.path)  # atomic, so a crash mid-write can't truncate the trail

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            entries = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(entries, list):
                return entries
        except json.JSONDecodeError:
            pass
        # Never wipe history: keep the unreadable file and start a fresh list beside it.
        self.path.rename(self.path.with_name(f"audit_trail.corrupt-{datetime.now():%Y%m%d%H%M%S}.json"))
        return []

    async def record_node(self, node: Any) -> None:
        """Log what one step of the agent loop did."""
        if Agent.is_model_request_node(node):
            # Results of the previous step's tool calls (and any retries) arrive with this request.
            for part in node.request.parts:
                if isinstance(part, ToolReturnPart):
                    await self.append(
                        "tool_result", step=self.step, tool_name=part.tool_name,
                        tool_result=short(part.content, RESULT_CHARS),
                    )
                elif isinstance(part, RetryPromptPart):
                    await self.append(
                        "retry", step=self.step, tool_name=part.tool_name,
                        tool_result=short(part.content, RESULT_CHARS),
                    )
            self.step += 1
            await self.append("model_request", step=self.step)
        elif Agent.is_call_tools_node(node):
            for part in node.model_response.parts:
                if isinstance(part, ToolCallPart):
                    await self.append(
                        "tool_call", step=self.step, tool_name=part.tool_name,
                        tool_args=short(part.args_as_dict(), ARGS_CHARS),
                    )

    async def end(self, stop_reason: str, usage: Any = None, **detail: Any) -> None:
        detail["duration_ms"] = round((time.perf_counter() - self.started) * 1000)
        if usage is not None:
            detail["usage"] = {
                "requests": getattr(usage, "requests", None),
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "tool_calls": getattr(usage, "tool_calls", None),
            }
        await self.append("run_end", step=self.step, stop_reason=stop_reason, detail=detail)


async def run_audited(agent: Agent, prompt: str, trail: AuditTrail, **run_kwargs: Any) -> tuple[Any, Any]:
    """Run an agent step by step, logging each node. Returns (output, usage); raises like agent.run()."""
    async with agent.iter(prompt, **run_kwargs) as run:
        async for node in run:
            await trail.record_node(node)
        return run.result.output, run.usage


def to_model_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn the browser's recent chat turns into PydanticAI message history."""
    recent = history[-HISTORY_TURNS:]
    while recent and recent[0].role == "assistant":  # history should open with the shopper
        recent = recent[1:]
    messages: list[ModelMessage] = []
    for turn in recent:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            content = turn.content
            if turn.product_ids:
                content += f"\n[Product cards shown with this reply: {', '.join(turn.product_ids)}]"
            if turn.page_title:
                content += f'\n[This reply put "{turn.page_title}" results on the page]'
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def _tools_called(messages: list[ModelMessage]) -> set[str]:
    return {
        part.tool_name
        for message in messages
        if isinstance(message, ModelResponse)
        for part in message.parts
        if isinstance(part, ToolCallPart)
    }


def _content_filtered(error: ModelHTTPError) -> bool:
    return error.status_code == 400 and "content_filter" in str(error.body)


async def run_chat(message: str, history: list[ChatTurn], deps: ShopDeps) -> ChatReply:
    """Answer one shopper message with the agent, logging every step to output/audit_trail.json."""
    trail = AuditTrail("chat")
    await trail.append(
        "run_start",
        detail={
            "shopper": f"user {deps.customer.user_id}" if deps.customer else "guest",
            "page": deps.page.path if deps.page else None,
            "viewing": deps.page.product.product_id if deps.page and deps.page.product else None,
            "message": short(message, MESSAGE_CHARS),
            "history_turns": len(history),
            "model": model_name(),
        },
    )
    usage = None
    try:
        output, usage = await run_audited(
            get_agent(),
            message,
            trail,
            message_history=to_model_history(history),
            deps=deps,
            usage_limits=USAGE_LIMITS,
        )
        stop_reason = "final_result"
    except ModelHTTPError as error:
        if not _content_filtered(error):
            await trail.end(f"error: ModelHTTPError {error.status_code}")
            raise
        output, stop_reason = ChatReply(reply=FILTERED_REPLY), "content_filter"
    except UsageLimitExceeded:
        await trail.end("usage_limit", note=f"stopped after {USAGE_LIMITS.request_limit} model requests")
        raise
    except AgentNotConfigured:
        await trail.end("not_configured")
        raise
    except Exception as error:
        await trail.end(f"error: {type(error).__name__}")
        raise

    if not output.product_ids:
        # The model sometimes names a product without listing it for a card; add exact-name matches.
        output.product_ids = products_named_in(deps.db_path, output.reply)
    await trail.end(
        stop_reason,
        usage,
        reply=short(output.reply, 160),
        product_ids=output.product_ids,
        page_results=output.page_results.title if output.page_results else None,
        cart_changed=deps.cart_changed,
    )
    return output


# ---------- Cart reminder emails ----------

EMAIL_MODE = """
## Email mode (this run only)

You are not chatting right now. You are writing the friendly words of a cart reminder email for the shopper
described in the message, following "Cart reminder emails" above. Ignore the chat-only rules about tools,
product_ids, and page_results. Return only `subject`, `opening`, and `closing`.
"""

# The model's words must not carry prices or stock counts; the code fills those in from the database.
NUMBERS_IN_COPY = re.compile(r"\$|\d+\s*%|\b\d+\s*(?:left|available|in stock|percent|off)\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def get_email_writer() -> Agent[None, CartEmailCopy]:
    """A second, tool-less agent that writes reminder email copy in the Campus Customs voice."""
    writer = Agent(_build_model(), output_type=CartEmailCopy, retries=2)

    @writer.instructions
    def email_prompt() -> str:
        return PROMPT_PATH.read_text(encoding="utf-8") + "\n" + EMAIL_MODE

    @writer.output_validator
    def no_prices_or_counts(output: CartEmailCopy) -> CartEmailCopy:
        text = " ".join([output.subject, output.opening, output.closing])
        if NUMBERS_IN_COPY.search(text):
            raise ModelRetry("Leave out prices, stock counts, and discounts; the email adds the real numbers itself.")
        if re.match(r"\s*(hi|hello|hey|dear)\b", output.opening, re.IGNORECASE):
            raise ModelRetry('Don\'t start the opening with a greeting; the email already begins "Hi {first name},".')
        return output

    return writer


async def write_cart_email(first_name: str, cart_view: CartView, user_id: int | None = None) -> tuple[str, str]:
    """Subject and body for one reminder: the model's friendly words around code-filled items and prices."""
    trail = AuditTrail("cart_email")
    await trail.append(
        "run_start",
        detail={"shopper": f"user {user_id}" if user_id else None, "cart_lines": len(cart_view.lines), "model": model_name()},
    )
    try:
        copy, usage = await run_audited(
            get_email_writer(),
            f"Shopper's first name: {_safe_name(first_name) or 'there'}\nTheir cart:\n{cart_facts(cart_view)}",
            trail,
        )
        subject, opening, closing_line = copy.subject, copy.opening, copy.closing
        await trail.end("final_result", usage, subject=subject)
    except Exception as error:
        # No model (or a model error): fall back to plain wording so the reminder is still drafted.
        subject, opening, closing_line = fallback_email_copy(first_name)
        await trail.end(f"error: {type(error).__name__}", note="used the fallback wording")
    return render_cart_email(first_name, cart_view, subject, opening, closing_line)


async def draft_cart_reminders(db_path: Path, idle_hours: float = 24) -> list[OutboxEmail]:
    """Draft one reminder per opted-in shopper whose cart has sat untouched for idle_hours. Nothing is sent."""
    drafts = []
    for idle in idle_carts(db_path, idle_hours):
        subject, body = await write_cart_email(idle.first_name, idle.cart, idle.user_id)
        drafts.append(save_email_draft(db_path, idle, subject, body))
    return drafts


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What hoodies do you have?"
    reply = asyncio.run(run_chat(question, [], ShopDeps(db_path=DB_PATH)))
    print(reply.reply)
    if reply.product_ids:
        print("cards:", ", ".join(reply.product_ids))
