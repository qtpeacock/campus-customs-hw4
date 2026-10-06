"""Draft cart reminder emails for shoppers who left items in their cart.

Meant to run on a schedule (for example once a day with cron or Windows Task
Scheduler). Each opted-in shopper whose cart has sat untouched for --idle-hours
gets one drafted email in the email_outbox table; they won't get another until
their cart changes. Nothing is sent: hooking up an email service would read the
drafts from email_outbox.

Run from HW4/:  python scripts/cart_reminders.py --idle-hours 24
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))  # the agent lives in backend/

from agent import draft_cart_reminders  # noqa: E402

DB_PATH = ROOT / "data" / "campus_customs.db"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--idle-hours", type=float, default=24, help="how long a cart must sit untouched (default 24)")
    args = parser.parse_args()

    drafts = asyncio.run(draft_cart_reminders(DB_PATH, args.idle_hours))
    print(f"{len(drafts)} reminder email(s) drafted.")
    for draft in drafts:
        print(f"\n--- #{draft.id} to {draft.to_email} ---\nSubject: {draft.subject}\n\n{draft.body}")


if __name__ == "__main__":
    main()
