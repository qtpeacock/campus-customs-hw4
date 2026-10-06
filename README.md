# Campus Customs: Yale Shop + AI Shopping Assistant

A customer website for Campus Customs (officially licensed Yale apparel, 57 Broadway, New Haven) with an AI shopping assistant.

- **Front end:** React + Vite + TypeScript.
- **Back end:** Python FastAPI, with a PydanticAI agent as the chatbot's brain.
- **Data:** a local SQLite database.

Shoppers can:
- browse products by type or collection,
- open a product page with live stock by size,
- create an account and log in,
- keep a cart,
- chat with an assistant that answers price and stock questions honestly from the database, puts matching products on the page, remembers logged-in shoppers, and can add to their cart.

## Repository layout

```
hw4/
├── AI_prompts.md            # prompt log for every problem
├── requirements.txt         # back-end Python packages
├── .env.example             # variable names with placeholders (copy to .env)
├── .gitignore
├── README.md
├── frontend/                # Vite React TypeScript app
├── backend/
│   ├── main.py              # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py             # ★ agent wiring: model, instructions, validator, audit trail, reminder emails
│   ├── models.py            # ★ Pydantic / PydanticAI structured types
│   ├── tools.py             # ★ tools the agent can call (+ shared catalogue and cart helpers)
│   └── prompts/
│       └── prompt.md        # ★ system prompt (voice, tool rules, policies, safety rules)
├── scripts/                 # optional one-time / scheduled helpers (see below)
└── output/
    ├── harness.md           # full system spec: models, tools, safety, specs, how it works
    ├── design.md
    ├── usability.md
    ├── app_check.html       # site test report (double-click to open)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # append-only log of agent-loop activity
```

The agent itself is the four ★ files under `backend/`.

**Local-only data pack (not in git):**

```
data/
├── campus_customs.db
└── products/                # images referenced by the catalogue
```

## What you need

- Python 3.11 or newer (tested with 3.13).
- Node.js 20 or newer (tested with 24).
- A Portkey API key. The agent calls an OpenAI-compatible model (`gpt-5.6-luna` by default) through Portkey.

## Setup

All commands run from the repository root (`hw4/`) unless noted.

1. **Place the data pack.** Unzip `data.zip` into the repository root so you have `data/campus_customs.db` and `data/products/`. The `data/` folder is in `.gitignore` and is never committed.

2. **Add your API key.** Copy `.env.example` to `.env` (in the repository root) and set `PORTKEY_API_KEY`.

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell, use `Copy-Item .env.example .env`. The real `.env` is git-ignored.

3. **Install the back end.** Using a virtual environment is optional but recommended.

   ```bash
   python -m venv .venv
   ```

   Activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Mac/Linux), then:

   ```bash
   pip install -r requirements.txt
   ```

4. **Install the front end.**

   ```bash
   cd frontend
   npm install
   ```

5. **(Optional) Polish the data.** The site works without these steps.

   ```bash
   python scripts/fix_catalogue.py
   ```

   Writes reviewed descriptions for three products whose catalogue text was a placeholder.

   ```bash
   python scripts/whiten_backgrounds.py
   ```

   Gives every product photo a white background (writes `data/products_white/`).

   `python scripts/import_worn_photos.py --hw3 ../HW3` copies "worn on campus" photos from the previous homework into `data/worn/`. It only works if that folder exists.

## Run it

Use two terminals.

**Back end** (FastAPI on port 8000):

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs. On first start, the back end adds the tables it needs (sessions, carts, email outbox) to `data/campus_customs.db`.

**Front end** (Vite on port 5173):

```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173**. Vite forwards `/api` and `/images` requests to the back end.

**Test account:** `test@campuscustoms.yale.edu` / `password`. You can also create your own on the site.

## Things to try

- Open the chat (bottom right) and ask **"What hoodies do you have?"** Matching cards fill the Products page.
- On a product page, ask **"Do you have this in XL? How many mediums are left?"** You get the real stock and price from the database.
- Log in, then say **"Add this in a large to my cart."** The cart badge updates, and `/cart` shows it.
- Use **Products → Type / Collection** in the nav, or the **Sort by** menu on the Products page.
- Staff preview of drafted cart reminder emails: http://127.0.0.1:5173/outbox. It works from the same computer, or with `ADMIN_TOKEN` set. Nothing is actually emailed.

## Other commands

| Command | What it does |
| --- | --- |
| `cd backend` then `python agent.py "your question"` | Ask the agent from the terminal |
| `python scripts/cart_reminders.py --idle-hours 24` | Draft reminder emails for opted-in shoppers' idle carts (meant for a daily schedule) |
| `cd frontend` then `npm run build`, or `npm run lint` | Type-check and build the front end, or lint it |

## Where to read more

- `output/harness.md`: how the whole system works, including every model and why its fields were chosen, the tools and abilities, safety rules, specs (loop limits, result caps, models), and the audit trail.
- `output/app_check.html`: screenshots proving honest stock answers, chat-driven search cards, and the saved cart.
- `output/audit_trail.json`: every agent run, step by step (append-only, never wiped).

## Notes

- **Kept out of git:** the real `.env`, `data/` (the database and product images), `node_modules/`, and build output.
- **Photo credits:** the Home page photos are from Wikimedia Commons under Creative Commons licenses; see `frontend/public/hero/CREDITS.md`.
