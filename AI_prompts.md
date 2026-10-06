# AI Prompts — HW4

This file records the prompts and evidence for each HW4 problem.

Each section includes the problem number and title, at least one prompt quoted in the user's words, a follow-up prompt if one was needed, and a sentence on what the first prompt was lacking.

## Problem 1 — Vibe Coder Prompts

### Prompts

- "no, restructure the AI_prompts_md to that there is one section for each problem (13), each section must have the problem number and title, at least one prompt i typed in my words and one follow-up prompt if i needed it and a sentence on waht it was lacking. this prompt i am typing now will be problem one, titled Vibe Coder Prompts. you dont need to include the things i said before this"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt gave the number of problems, the parts every section needs, and the title for Problem 1, so no follow-up was needed.

### Evidence

- Restructured `HW4/AI_prompts.md` into 13 problem sections, each with the problem number and title, prompts, follow-up prompt, and what the first prompt was missing.
- Filled in Problem 1; Problems 2–13 hold placeholders until each problem is given.

## Problem 2 — Analyze the Database

### Prompts

- "cool. problem 2: analyze the database: look at the database data/campus_customs.db and understand the fields of each table. at a minimum i should understand catalogue, inventory, and users. start the file output/harness.md. write down each table and its fields, and one short line on why each field matters for the shop or the chatbot. You will keep growing this harness file in later problems (models, tools, safety, specs)."

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt named the database, the tables to cover, the output file, and the one-line-per-field format, so no follow-up was needed.

### Evidence

- Read the schema and data of every table in `data/campus_customs.db`: `catalogue` (102 rows), `inventory` (612 rows), `users` (3 rows), `chat_messages` (22 rows), and SQLite's `sqlite_sequence`.
- Started `output/harness.md` with a Database section: each table, every field with its type, and one line on why it matters for the shop or the chatbot.
- Recorded the table relationships (`catalogue` → `inventory` on `product_id`, `users` → `chat_messages` on `user_id`).
- Added data notes for later problems: 145 sold-out product–size rows, the $32–$98 price range, 22 inconsistent `garment_type` spellings, JSON-encoded `colors` and `search_tags`, all image paths valid, and the `pbkdf2_sha256$salt$digest` password format.

## Problem 3 — Build the Campus Customs Website

### Prompts

- "okay, problem 3: build the campus customs website: scaffold a react + vite + typescript front end for campus customs. put a nav bar at the top that links to the main pages: home, products, about us, log in, create account. pull campus custons-style wording from yalebulldogblue.com for home and about us sections, but write these pages in my voice (based on our conversations) do not copy original site text. on the products page, show product images from the catalogue (use the image paths in the database) with basic product info (name, price, short description). make each product open a single-item page (large image on one side, full product text on the other - description, price sizes/stock when you have them). clicking a card on production should take the shopper there. add a chat interface in the bottom right of the site (a floating chat panel is fine). it does not need to talk to an agent yet - a stub that will call your backend later is enough for this problem. you will need a small api soon to read the database. it is fine to start a simple FastAPI in backend/main.py just to serve products and images, then grow it into the agent backend in Problem 5."

### Follow-up prompt

- None needed.

### What the first prompt was missing

No follow-up was needed; the only open point was what Log In and Create Account should do before accounts exist, so they were built as working forms with a "coming soon" message until the backend supports them.

### Evidence

- Researched yalebulldogblue.com (homepage, refund policy, shipping policy, contact page) and news coverage of Campus Customs for style and facts: Yale blue `#00366b` with near-black text and white, the 57 Broadway New Haven store, family-run since the 1970s, officially licensed, 30-day unworn-with-tags returns, custom items final sale, 5–8 business-day production, UPS and international shipping, `orderdept@campuscustoms.com` and (475) 301-4205. All page copy was written fresh in a casual first-person voice, not copied.
- Created `backend/main.py`, a FastAPI app that opens `data/campus_customs.db` read-only and serves `GET /api/health`, `GET /api/products` (all 102 products), and `GET /api/products/{product_id}` (one product plus stock for each size, ordered XS–XXL, 404 if missing). It serves only `data/products/` at `/images/products/...`, so the image paths come straight from `catalogue.image_file_path` and the database file itself is not reachable. It runs with `python backend/main.py` and no auto-reloader.
- Scaffolded `frontend/` with React + Vite + TypeScript and React Router; Vite proxies `/api` and `/images` to the backend on port 8000.
- Built the nav bar (Home, Products, About Us, Log In, Create Account, with a mobile menu), Home (hero, four featured products from the database, value strip), About Us, Products (grid of all 102 cards with image, name, price, and a two-line description), the single-item page (large image left; name, price, description, colors, and per-size stock showing In stock / Only N left / Sold out on the right), Log In and Create Account forms, and a not-found page.
- Added a floating chat panel in the bottom-right corner (`ChatWidget.tsx`) that keeps the conversation across page changes; `sendChatMessage` in `api.ts` is a stub that replies locally until the agent endpoint exists in Problem 5.
- Styled everything in black, Yale blue, and white with accessible contrast. 73 of the 102 product photos have black backgrounds and 29 have white, so photos fill their frames edge to edge.
- Added `HW4/.gitignore` that keeps `data/`, `data.zip`, `*.db`, `.env`, `node_modules/`, and build output out of the repo.
- Verified: `npm run build` and `npm run lint` pass with no errors or warnings; in the browser the products page shows 102 cards, clicking a card opens its item page with correct stock (e.g. Baseball Left Chest Crewneck: XS and XL sold out, M "Only 5 left"), the chat stub replies and survives navigation, the forms validate, and the mobile menu works.

## Problem 4 — Create Account and Login

### Prompts

- "problem 4: create account and login: build a normal create-account/login flow: create account (first name, last name, email, password (confirm password if it works), log in (email and password). new accounts go into the users table. make sure to store passwords securely so hackers (human or AI) cannot access them. the seed database already has a test user you can use while building. Email (test@campuscustoms.yale.edu), password (password). confirm you can log in as that user, and that a brand-new account you create also works. update output/harness.md with how auth works (what you store for a user and how passwords are protected)"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt gave the form fields, where accounts are stored, the security goal, the test user's login, what to confirm, and what to add to the harness, so no follow-up was needed.

### Evidence

- Worked out the seed hash format by testing the test user's known password: `pbkdf2_sha256$<salt>$<digest>` with 120,000 PBKDF2 iterations.
- Created `backend/security.py`: PBKDF2-HMAC-SHA256 hashing with 600,000 iterations and a random 16-byte salt per user (`pbkdf2_sha256$600000$<salt>$<digest>`), verification of both the new and the seed format with a constant-time comparison, automatic upgrade of seed hashes at the next login, a dummy hash for unknown emails so timing doesn't reveal which accounts exist, random session tokens stored only as SHA-256 hashes, and a failed-login limiter (5 per email, 20 per IP, per 15 minutes).
- Added `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, and `GET /api/auth/me` to `backend/main.py`, plus a `sessions` table created at startup. Sessions use an `HttpOnly`, `SameSite=Lax`, 7-day `cc_session` cookie, and no response ever includes `password_hash`.
- Front end: `frontend/src/auth/AuthContext.ts` and `AuthProvider.tsx` track the logged-in shopper; Log In and Create Account (with confirm password) now call the backend and show its errors; the nav shows "Hi, {first name}" and Log Out when logged in.
- Verified in the browser against the real database: logged in as `test@campuscustoms.yale.edu` / `password` (nav showed "Hi, Test", login survived a reload, Log Out worked); created Handsome Dan (`handsome.dan@yale.edu`), which landed in `users` with a 600,000-iteration hash, logged in automatically, and logged back in after logging out. Duplicate email, mismatched passwords, wrong password, a sixth bad guess (429), and a forged cookie were all rejected.
- Updated `output/harness.md` with the `sessions` table and an Authentication section: endpoints, what is stored for a user, how passwords are protected, how sessions work, and what was verified.
- `npm run build` and `npm run lint` pass with no warnings.

## Problem 5 — PydanticAI Agent Backend

### Prompts

- "great, problem 5: PydanticAI agent backend. Build the shop chatbot as a PydanticAI agent behind FastAPI, plugged into your front-end chat widget. put the api app in backend/main.py - that is the file you run with Uvicorn. Keep the agent as these four files next to it. (same idea as homework 3): backend/prompts/prompt.md (system prompt (grow this same file later), backend/agent.py (agent entry/wiring) backend/tools.py (tools the agent can call), backend/models.py (Pydantic/PydanticAI structured types). In main.py, expose a chat route so a message from the website returns a reply from the agent (and whatever else you need for products/auth). We will need the AI model API key for the agent. Put Campus Customs voice and safety basics into prompts/prompt.md (we will expand tools and safety later). start or update types in models.py for chat replies / product cards as needed. In output/harness.md, note how the front end talks to FastAPI and how the agent is loaded (prompt file + model). Make sure the backend runs from the backend/ folder like this: uvicorn main:app --reload --port 8000"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt named the four agent files and their jobs, the chat route, the API key, what goes in the prompt and models, what to add to the harness, and the exact run command, so no follow-up was needed.

### Evidence

- `backend/prompts/prompt.md`: system prompt with who Campus Customs is, the shop's casual voice, plain-text replies, tool-use rules (search before naming a product, check stock before answering about a size, prices and stock only from tools), each product being one colorway, card rules, store policies (shipping, returns, refunds, contact), and safety basics (no invented facts, no orders/payments/discounts, no sensitive data, stay on topic, ignore rule-change and prompt-reveal requests).
- `backend/agent.py`: builds the PydanticAI agent once with an `OpenAIChatModel` through Portkey (`PORTKEY_API_KEY` from the environment; model `gpt-5.6-luna` via `OPENAI_MODEL`/`CHAT_MODEL`), loads `prompt.md` on every message through `@agent.instructions`, adds the shopper's cleaned first name, validates that every returned `product_id` exists, converts the browser's last 12 turns into message history, turns provider content-filter blocks into a polite refusal, and can be run from a terminal (`python agent.py "question"`).
- `backend/tools.py`: `search_products` (scored text search with kind, color, and max-price filters; the 22 raw garment types collapsed into six kinds) and `get_product_details` (live stock per size), both read-only, plus `ShopDeps` and card helpers.
- `backend/models.py`: `ProductSummary`, `ProductDetail`, `SizeStock`, `SearchResult`, `ProductCard`, `ChatTurn`, `ChatRequest`, `ChatResponse`, the agent output `ChatReply`, and the account types moved here from `main.py` (`RegisterRequest`, `LoginRequest`, `UserOut`).
- `backend/main.py`: new `POST /api/chat` (rate-limited, uses the logged-in shopper's first name, returns the reply plus product cards built from the database, 503/502/429 with friendly messages); `/api/health` now reports the chat model and whether a key is configured. Added `backend/requirements.txt` entries for PydanticAI, OpenAI, and python-dotenv, and `HW4/.env.example` with placeholder variable names.
- Front end: the chat widget now calls `/api/chat` with recent history (including which product cards were shown), greets logged-in shoppers by first name, shows clickable product cards under replies, displays backend errors, and starts a fresh conversation on log in or log out.
- Fixed during testing: the model first described the Basic Hoodie as coming "in navy blue or white", so the prompt and the `colors` field description now say each item is one colorway; follow-ups lost track of products, so history turns now carry their product ids and a reply that names a product by its exact name gets its card; a jailbreak message hit the provider's content filter and returned an error, so it now gets a polite refusal.
- Verified: `uvicorn main:app --reload --port 8000` runs from `backend/` (then its whole process tree was stopped); in the browser, "I need a gift for my dad, something warm" returned the Yale Dad Hoodie ($68) and Yale Dad Crewneck ($58) as cards, and "is the hoodie available in XL?" answered "12 left", matching `inventory`; through the API, the sold-out XL baseball crewneck, the no-pink answer, the return policy, the jailbreak refusal, and the off-topic refusal all behaved correctly. `npm run build` and `npm run lint` pass.
- Updated `output/harness.md` with how the front end talks to FastAPI (Vite proxy, endpoints, the chat request/response and flow) and how the agent is loaded (prompt file, model, Portkey key, output type, validator, limits, history), the first tools, and the prompt's safety basics.

## Problem 6 — Tools: Product Info and Stock

### Prompts

- "great. problem 6: tools: product info and stock: give the agent tools that look up real information from campus_customs.db: product description, price, how many are in stock (by size when the customer asks). the agent must use the database - it should not invent prices or quantities. if a size is out of stock, say so clearly. expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. add or update return types in models.py. in output/harness.md, list each tool and explain which model fields you chose for lookup results and why."

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt named the facts to look up, the no-inventing rule, how to handle out-of-stock sizes, and the prompt, models, and harness updates, so no follow-up was needed.

### Evidence

- `backend/tools.py`: replaced the single details tool with three read-only database tools: `search_products` (now with a `size` in-stock filter, `sizes_in_stock` on every match, and a `sold_out_in_size` list of matches hidden by that filter), `get_product_info` (description, exact price, colors, kind, sizes offered), and `check_stock` (live stock for one size or all sizes, plus price). Both product lookups accept a product_id or exact name and return suggestions when nothing matches. Size words like "medium", "extra small", and "2XL" are normalised, and stock status (sold out / low at 1–5 / in stock) is decided in code.
- `backend/models.py`: added `ProductInfo`, `StockReport`, `ProductNotFound`, a `status` on `SizeStock`, `sizes_in_stock` on `ProductSummary`, and `sold_out_in_size` on `SearchResult`; removed the old `ProductDetail`.
- `backend/agent.py`: the output validator now makes the model retry if a reply quotes a price or stock level without having called a product tool for that message. A scripted fake-model test showed an invented "$49" being rejected, followed by a `check_stock` call and the real $58.
- `backend/prompts/prompt.md`: new "Price and stock questions" section with a question-to-tool table, how to word sold-out, low-stock, and size-not-offered answers, checking stock fresh every time, never promising restocks, and answering about the exact product named.
- Fixed during testing: asked whether the Baseball Left Chest Crewneck came in XL, the agent searched with an XL filter, which hid that sold-out item, and it answered "yes" about a different crewneck. Search now reports items hidden by the size filter, and the prompt requires checking a named product directly and never swapping products silently. On retest it correctly said "sold out in XL" and listed the sizes in stock.
- Verified against `inventory`: the sold-out XL baseball crewneck, "only 5 left in M" for the Basic Hoodie Big Yale, "isn't made in 3XL" for the Champion crewneck, the Benjamin Franklin Fleece Jacket sold out in XS and XXL, nine quarter-zips in XXL, and in the website chat "$98" → "sold out in XXL" → "only 2 left in L" with product cards.
- Updated `output/harness.md` with a "Tools: product info and stock" section: each tool, its arguments and return type, a field-by-field explanation of every lookup result model and why each field was chosen, the guarantees enforced in code, and the verified answers.

## Problem 7 — Chat Search That Updates the Page

### Prompts

- "problem 7:  chat search that updates the page: now we will add another feature to the site. when a customer asks about a type of item - for example \"what hoodies do you have\" - the agent should search the catalogue and the website should dynamically show those matching items as product cards (image, name, price, short info). This is an API contract: the agent returns structured product matches and then the front end renders them on the website. make sure it looks cool. after the dynamic product cards are loaded by the new feature, make sure the same single-item page behavior we build in problem 3 still works: each product card - including the ones the chat just put on the page - should still open that detail view (large image + full info) when clicked. update prompts/prompt.md and output/harness.md so it is clear how search results reach the page."

### Follow-up prompt

- "okay, flag those photos in my md notes somewhere, but using the photo, create text descriptions for them and colors. also, can you make sure every item has a white background
double check those descriptions with me also"
- "those look good, go ahead and add them"

### What the first prompt was missing

The first prompt covered the feature but not the catalogue data behind the cards, so the follow-up asked to flag the three products with placeholder descriptions, write real descriptions and colors from their photos (checked with me first), and give every product photo a white background.

### Evidence

- API contract: the agent's output `ChatReply` now has `page_results: PageSearch` (a title plus the `CatalogueFilters` that found the items). `main.py` turns it into `ProductMatches` with `tools.page_matches()`, which re-runs the same search through the shared `find_products()` and builds every `ProductMatch` from the database (image, name, price, short description, colors, sizes in stock, plus count and price range). `ChatResponse` returns `reply`, chat `products`, and `page_results`. An output validator rejects page filters that match nothing.
- Front end: new `ChatPageContext`/`ChatPageProvider` (results kept in `sessionStorage`), `ChatResults.tsx` (a "From your chat" gradient banner with title, count, price range, filter chips, "Refine in chat" and "Show all products"), a generalised `ProductCard` with size chips and a staggered entrance plus glow (off for reduced-motion users), a chip in the chat that brings results back, and on narrow screens the chat panel tucks away when results land.
- Detail pages: every card, including chat-loaded ones, links to `/products/{id}`; product pages opened from chat results say "Back to Hoodies", and going back keeps the results.
- `prompts/prompt.md`: new section "Product cards in the chat, and search results on the page", covering when to set `page_results`, copying the exact search filters, structured filters over free text, titles, short replies, and counts and ranges from `total_matches`/`price_min`/`price_max`.
- Fixed during testing: the agent first gave a wrong price range ($68–$88 instead of $45–$88) from a partial list, so search results now include the full range; "navy crewnecks" matched gray ones with navy print, so the color filter uses the garment's main color; "red" matched inside "embroidered", so search terms match at the start of words; outline buttons rendered with the browser's gray background, now transparent.
- Data issue found: three catalogue rows have a placeholder description ("Vision blocked; filename-based stub") and no colors. The agent now gets an empty description for them and the site shows a friendly fallback line; the database was left unchanged.
- Verified in the browser: "what hoodies do you have?" moved the site from Home to `/products` with "Hoodies · 27 matches · $45–$88" and all 27 animated cards; "show me navy crewnecks under $60" and "which of those are under $60?" refined the page; single-product, policy, and not-carried questions left the page alone; clicking a chat-loaded card opened its single-item page (large image, $88, description, size stock); "Back to Hoodies" and "Show all products" worked. No console errors; build and lint pass.
- Updated `output/harness.md` with "Chat search that updates the page": a step-by-step of how results reach the page, the JSON contract for the agent output and API response, a field table for each new model, what the shopper sees, detail-page behavior, prompt rules, fixes, and verification.
- Follow-up: flagged the three placeholder products (Benjamin Franklin T Shirt, Berkeley Sweater Fleece Jacket, Timothy Dwight College Crewneck) in a "Flagged products" table in `output/harness.md`, and drafted descriptions, colors, garment types, and search tags for them from their photos. After approval, `backend/fix_catalogue.py` wrote them into the database (re-runnable on a fresh `data.zip`). Verified on the live site and in chat that the new descriptions are used and no placeholder rows remain.
- Follow-up: added `backend/whiten_backgrounds.py`, which writes white-background copies of all 102 photos to `data/products_white/` (73 black backgrounds whitened, one black frame line removed, 28 copied as-is) without touching the originals. `main.py` serves that folder, with a version on image URLs so browsers don't show cached black copies. The first threshold chewed the edges of dark navy hoodies and was lowered after a visual check. Product cards went back to a white store-style frame. All 102 served images were checked for white corners.

## Problem 8 — Customer Memory

### Prompts

- "great. problem 8: customer memory: when a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name, email) - put that in agent deps (or an equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks, \"do you  have this in pink?\", the agent knows which item they mean. Hint- put this code into the agent context. guests can still chat, but history only needs to persist for logged-in users. Document in output/harness.md: how user chat history is stored, what customer fields the agent sees and how page context is passed"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt said what to store and when, what the agent must know, the product-page example, guest behavior, and exactly what to document, so no follow-up was needed.

### Evidence

- History storage: uses the existing `chat_messages` table (plus an added `page_json` column and a `(user_id, id)` index created at startup). After each reply to a logged-in shopper, `main.py` saves the message and the reply (with its product cards and page search) in one transaction; guests are never saved. New `GET /api/chat/history` (latest 50, cards rebuilt from the catalogue, page searches re-run) and `DELETE /api/chat/history` (own rows only). For logged-in shoppers the agent's history now comes from the database, not the browser.
- Customer in agent deps: `ShopDeps` now holds `customer: CustomerProfile` (user_id, first/last/full name, email, member since, saved message count) and `page: CurrentPage`. An `@agent.instructions` function adds a "Right now" block with the shopper's name and email (sanitised) and their page. New tools `get_customer_profile` and `get_current_page` return the same data.
- Page context: the chat widget sends `page` (`path`, `product_id` from `/products/{id}`, `results_title`) with every message. `resolve_page()` validates the product against the catalogue into a `ViewedProduct`, and the "Right now" block tells the agent that "this"/"it" means that product. The chat shows "Looking at {product}" on product pages.
- `prompts/prompt.md`: new section "Who you're talking to, and what page they're on" (using the profile, privacy, "this" on product pages, the pink example, "these" on results), and the safety rule now covers other shoppers' data.
- Front end: the chat loads saved history for logged-in shoppers ("Welcome back, {name}! Here's where we left off."), has a "New chat" button, says when the chat is saved, strips old markdown in seed messages, and sends page context.
- Verified with API tests on a database copy: seed history reloads with rebuilt cards; on the Baseball Left Chest Crewneck page "do you have this in pink?" and "is it in stock in a medium?" were answered about that item; "who am I…?" returned the right name and email; 4 messages saved 8 rows; "what was I looking at last time?" after re-login answered "quarter-zips"; a new account saw no one else's history and the agent refused to share it; guests saved 0 rows and couldn't delete.
- Verified in the browser as Handsome Dan: "do you have this in pink?" on the Pierson College Crewneck page and "how about in large?" (sold out in L, matching `inventory`); a reload and a log-out/log-in both restored the 6 saved messages; "what was I asking you about before?" summarised them. No console errors; build and lint pass.
- Testing note: an early test hung because three test clients, each with its own event loop, shared one cached model-provider connection; real uvicorn runs a single loop, and the test was rerun with one client.
- Updated `output/harness.md` with "Customer memory and page context": how history is stored (table, columns, write, read, and delete paths), which customer fields the agent sees and how (deps, instructions, tool), how page context flows from the website to the agent, and what was verified. Older lines that said history lived in the browser were corrected.

## Problem 9 — Usability Improvements

### Prompts

- "problem 9: usability improvements: now we are going to improve the core shop. we will choose and implement 2 front end usability and 2 agent/backend usability improvements: for the two front end: add a photo carousel behind the home site where it says \"yale gear you'll actually wear\", use stock photos of yale students/athletics but dim them so the words are easy to use\", then for the second thing, sort the items by t-shirt, hoodie, etc, and add a drop down menu in the products tab to sort, make this like a typical clothing website would have. once we complete these we will move onto the back end usability"

### Follow-up prompt

- "before backend - quick note - write output/usability.md as we build, make one section for each of the 4 change. add max 2 sentences to summarize what we did. after we finish the backend, prompt me to fill out an additional section for each change and prompt me to fill out what i added in my own words, and why it helps a campus customs shopper or the business"

- "okay. for backend - im not sure what to fix, does the user data save items that the user has looked at? can we make a shopping cart that will hold items people \"add to cart\" and then store that data (for users only) and create emails to send those people later?, can you give me like 5 examples of backend fixes with those ideas in mind?"
- "can you do 1 and 3 as one improvement and then also 5 as the second backend improvement"

### What the first prompt was missing

The first prompt named the two front-end changes but left the two backend changes open, so the follow-ups asked what data was saved, picked ideas from five suggested backend fixes (a saved cart with reminder emails, and a chatbot that uses the cart), and set up `output/usability.md` to track all four.

### Evidence

- Front end 1, home photo carousel: five Yale photos from Wikimedia Commons (football players at the Yale Bowl, students on Old Campus, cheerleaders, a hockey game at Ingalls Rink, the marching band; CC BY-SA 3.0, CC0, CC BY 4.0), resized to 1600px and compressed to about 1.6 MB total in `frontend/public/hero/`, with `CREDITS.md` and `src/heroSlides.ts`. `HeroCarousel.tsx` crossfades every 6 seconds with a slow zoom under a dark gradient overlay so the white headline stays readable, and it loads photos only as they're needed. It has a pause/play button and dots (24px tap targets), shows the author and license of the photo on screen as CC BY/BY-SA require, and doesn't auto-advance for reduced-motion users.
- Front end 2, shop by type with sorting: the products API now returns each item's `kind` (hoodie, crewneck, t-shirt, quarter-zip, jacket, long-sleeve; the same grouping the agent uses). The nav's Products link has a "Shop by type" dropdown that opens on hover, keyboard focus, or the arrow button, and becomes an indented list in the mobile menu. The Products page has category tabs with counts (All 102, Hoodies 27, Crewnecks 29, Quarter-Zips 11, T-Shirts 25, Long Sleeve 2, Jackets & Fleece 8), a "Sort by" dropdown (Featured, Price low–high and high–low, Name A–Z and Z–A), and an All/Featured view grouped into sections by type. Category and sort live in the URL (`?category=hoodies&sort=price-asc`), and product page breadcrumbs now read Products / Hoodies / item.
- Verified in the browser: the carousel advances on its own, jumps with the dots, stops with pause, and shows the right credit; screenshots show Ingalls Rink and the football team dimmed behind readable text, on desktop and phone. The dropdown lists all six types and "Shop all"; Hoodies showed exactly 27 items; price sorting was in order both ways; All/Featured showed 102 items in six sections; on a phone the categories sit in the menu, tabs scroll sideways, and nothing overflows. No console errors; build and lint pass.
- Started `output/usability.md` with one section per change. Each has a summary of at most two sentences, plus placeholders for "what I added, in my own words" and "why it helps a Campus Customs shopper or the business" to fill in after the backend half. The two front-end summaries are written; the two backend sections are waiting on those changes.
- Answered the follow-up question: the site didn't record product views or have a cart; it saved accounts, sessions, and chat history (including cards shown). Suggested five backend ideas: a saved cart, recently viewed items, abandoned-cart email drafts, back-in-stock alerts, and chat cart tools.
- Backend 1, saved cart and cart reminder emails: new `backend/cart.py` with `cart_items` and `email_outbox` tables and a `users.cart_emails` opt-in, all created at startup.
  - Cart rules are enforced server-side: sold-out sizes, sizes not made, and unknown products are refused; quantities are capped at stock and 10 per line; every read is priced and stock-checked live.
  - Endpoints for the cart (get, add, change, remove), a guest-cart preview, a merge at login, the opt-in preference, and the staff outbox.
  - Reminders: `idle_carts()` finds opted-in shoppers whose cart sat untouched for N hours and who haven't been reminded since the last change. A second, tool-less agent writes the subject, opening, and closing (validator blocks prices, counts, discounts, and greetings; fallback wording if the model is down). The code fills in the items, prices, stock notes, subtotal, link, and opt-out line, and saves it as a draft.
  - Runs from `python cart_reminders.py --idle-hours 24` or the staff `/outbox` page.
- Backend 2, chatbot uses the cart: new agent tools `view_cart`, `add_to_cart`, `remove_from_cart`, and `get_shopping_activity`, for logged-in shoppers only; they're the agent's only writes, limited to the shopper's own cart. `ChatResponse.cart_changed` refreshes the badge. A new prompt section, "The shopping cart", says to add only on clear request with a size, never on its own, report results honestly, and explain there's no checkout yet. A new "Cart reminder emails" section sets the email voice.
- Front end for both: size chips are now buttons with a quantity menu and Add to cart; there's a nav cart badge; a `/cart` page with steppers, stock notes, subtotal, "Checkout coming soon", and the reminder checkbox; an opt-in checkbox on Create Account; the staff `/outbox` preview page; and a `CartProvider` that keeps guest carts in the browser and merges them at login.
- Fixed during testing: the email writer started its opening with "Hi Test," on top of the code's greeting (now blocked by the prompt and validator); the number check missed "20% off" (fixed); "×" in cart messages made test output unreadable (reworded).
- Verified with API tests on a database copy:
  - Refusals and caps: a sold-out size, a size the product isn't made in, and an unknown product were refused; 5 requested with 2 left became 2; the guest preview capped and flagged correctly.
  - Saving: merge, quantity changes, and removal saved correctly.
  - Reminders: one reminder per cart state; no reminder for a fresh cart at 24 hours; 403 without the staff token.
  - Chat (logged in): it asked for a size, then added; refused sold-out XL; removed on request; gave a cart rundown and suggestions.
  - Chat (guest): pointed to the button or logging in, and nothing was saved.
- Verified in the browser as Handsome Dan:
  - Adding 2 in M from a product page set the badge to 2; chat "add the yale dad hoodie in large" set it to 3; the cart page steppers changed the total to $194.
  - The reminder opt-in saved, and `/outbox` drafted one correct email, with no duplicate on a second click.
  - A guest cart item merged into Dan's cart at login.
  - No console errors; build and lint pass.
- Filled in "What we did" (at most two sentences) for both backend changes in `output/usability.md`, and added the cart, email, and chat-cart tables, endpoints, tools, and checks to `output/harness.md`.

## Problem 10 — Style the Website

### Prompts

- "problem 10: style the website: we will add creative design so the site feels like a real campus customs storefront - fonts, color, hierarchy, motion, product presentation, chat feel.  give me 8 examples of simple and sleek ways we can do this, i will pick a few and tell you some of my own ideas as well"

### Follow-up prompt

- "lets do 6 - so lets do - #1, #2, #3, #4, #8 (but add these options to the drop down products menu, within that, have a dropdown for Type (which includes t-shirt, sweatshirt, etc), and a dropdown for Collection (which includes family , sports, colleges, etc). for the last item (do this last), look back to the photos we worked on in our previous homework, if there is a match from the idem in the photo to the item on this website, add it into the photo for that item in a carosel (it should work that when you move your mouse over the basic product photo, it shows the other photo, and when you are on that product page, you can toggle between the two photos). then, write in output/design.md what we changed and why it should help customers stick around and buy. keep it less than 4 sentences."

### What the first prompt was missing

The first prompt asked for eight ideas to choose from, so the follow-up had to pick five of them (type, header and logo, varsity details, product cards, shop-by tiles), add the Type and Collection dropdowns inside the Products menu, add the HW3 photo matches as a second photo on those products, and ask for a short `output/design.md`.

### Evidence

- Gave eight design ideas (type pairing, logo and header, varsity details, product cards, product page, motion, chat feel, shop-by tiles).
- #1 Type: self-hosted Libre Caslon Display and Text for headlines and prices, Inter for text, and Barlow Condensed for uppercase varsity labels (`@fontsource` packages, latin subsets; no font CDN).
- #2 Header: a shield "CC" monogram logo (`Logo.tsx`) with "Yale Bulldog Blue · New Haven"; the announcement bar rotates four true messages (pauses on hover, still for reduced motion) and collapses on scroll; the header slims and frosts once the page scrolls.
- #3 Varsity details: navy-and-white stripe bands under the hero, above the footer, and under each tile photo; faint outline shields behind section headings; a round "Campus Customs · New Haven · Since the 1970s" seal in the hero and footer; striped catalog section underlines.
- #4 Product cards: photo zoom on hover; honest stock badges from live inventory ("Only 2 left in XL", "Sold out in M", "Limited sizes"); a serif price; Quick add (pick a size right on the card, with the cart badge bumping); shimmering placeholder cards while products load. The products API now returns per-size `stock` for this.
- #8 Shop by: the backend tags every product with collections (Residential Colleges 19, Sports & Teams 36, Yale Family 12, Grad & Professional Schools 13, Classic Yale 22; every product is in at least one). The Products menu now has Type and Collection dropdowns inside it (flyouts on desktop, tap-to-open lists on phones). The Home page has five "Shop by collection" tiles. The Products page filters by collection too (a Collection menu next to Sort; titles like "Hoodies · Yale Family").
- Last item, HW3 photo matches: HW3's identify results matched two photos (the gray "YALE University DAD" tee outside SOM to the Yale Dad T Shirt, and the navy "YALE Bulldogs" long sleeve to the Dry Zone Long Sleeve). `backend/import_worn_photos.py` copies confident matches into `data/worn/<product_id>.jpg` (kept out of GitHub since they show real people). The API returns them as `extra_images`; hovering over those cards swaps to the worn photo; product pages get a two-photo gallery with arrows, labeled thumbnails, and a "2 / 2 · Worn on campus" counter.
- Fixes during the work: "crew" put a Champion raglan crewneck under Sports, so the rule now matches "Crew Left Chest"; one announcement overstated things and was reworded to match the policy; seal ids are now unique for pages with two seals; submenus open on hover only for a mouse, so a tap on a phone isn't undone; the worn photo loads up front so the hover swap is instant.
- Verified in the browser:
  - All four fonts loaded and are applied; the header frosts and slims on scroll.
  - The Collection flyout links work: Yale Family showed 12 items in three type groups; "Hoodies · Yale Family" showed exactly the six family hoodies; switching the menu to Sports showed 14 hoodies.
  - Quick add put a medium Basic Hoodie in the cart, showed "Added M ✓", and bumped the badge from 4 to 5.
  - The Yale Dad T Shirt card swaps to the worn photo, and its product page toggles between both photos with the arrows and thumbnails.
  - On a phone, the Type list opens with a tap and filters to Quarter-Zips, and nothing overflows. No console errors; build and lint pass.
- Wrote `output/design.md` (three sentences) on what changed and why it should help shoppers stick around and buy.

## Problem 11 — Site Testing (App Check)

### Prompts

- "problem 11: site testing (app check): test the live site and document it in output/app-check.html (a page you can double-click open). we have to include clear screenshots and short captions for: chat checking the inventory level of an item (honest stock/price from the DB), the dynamic search-result cards appearing after a category questions (e.g. hoodies), one of the usability features you added in problem 9. Make the HTML easy to grade: heading for each check, screenshot, one or  two sentences on what the screenshot proves. put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (for example app_check_images/inventory.png) can you do this yourself? what do you need me to do?"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing needed a follow-up; the prompt named the report two ways (`app-check.html` and `app_check.html`). It was first saved as `app-check.html`, then renamed to `output/app_check.html` in Problem 13 to match the final file tree.

### Evidence

- Answered the question: everything could be done without help, by using Playwright to drive Microsoft Edge (already installed) against the running site.
- Captured five 1920×1080 PNGs in `output/app_check_images/` with motion turned off, reading the database right after each step:
  - `inventory.png`: guest on the Baseball Left Chest Crewneck page asked "Is this in stock in XL? How many mediums are left, and what's the price?"; the agent said sold out in XL, only 5 mediums left, $58, matching `inventory` (XS 0, S 15, M 5, L 25, XL 0, XXL 25) and the $58 catalogue price.
  - `search_results.png`: guest asked "What hoodies do you have?" on the home page; the site moved to `/products` with a "Hoodies · 27 matches · $45–$88" banner and 27 hoodie cards, matching the database (27 hoodies, $45–$88), and clicking the first card opened its product page.
  - `cart_chat.png`, `cart_page.png`, `cart_email.png` (Problem 9 saved cart): a new test shopper (Casey Checker) signed up with reminders on and asked "Please add this hoodie in a large to my cart" on the Yale Mom Hoodie page. The agent added it, the cart badge showed 1, the cart page showed the $68 line with the opt-in checked (one `cart_items` row, `cart_emails = 1`), and the staff outbox drafted "Your Yale Mom Hoodie Is Waiting" with the real item and subtotal (status `draft`).
- Wrote the report (now `output/app_check.html`): a summary table with PASS for each check; a heading, screenshot (relative path, click for full size), and two-sentence "What this proves" caption per check; expandable chat transcripts and database values; and a note on how the screenshots were captured. Opened it from the file in Edge and confirmed all five images load; fixed low-contrast code labels in the header.

## Problem 12 — Audit Trail, Safety, Finish Harness

### Prompts

- "problem 12: audit trail, safety, finish harness: keep an append-only output/audit_trail.json of the agent loop activity (time, tool name, short args/result, stop reason). Do not wipe it between runs. also think of some safety rules to give to the agent and put them in prompts/prompt.md. finish output/harness.md so it is clear how the system works. model fields in models.py and why you chose them, tools and abilities, safety rules, specs (loop limits, result caps, models, how to run front + back)"

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt listed what the audit trail must record and that it must never be wiped, asked for safety rules in the prompt, and named every part the finished harness needed, so no follow-up was needed.

### Evidence

- Audit trail: new `backend/audit.py` and an `AuditEntry` model in `models.py`.
  - What it covers: every chat message and every reminder email runs through `run_audited()`, which walks the agent loop node by node and appends `run_start`, `model_request`, `tool_call`, `tool_result`, `retry`, and `run_end` entries.
  - Each entry holds a UTC timestamp, run id, step number, tool name, short redacted args and result, the stop reason (`final_result`, `content_filter`, `usage_limit`, `not_configured`, or `error: <type>`), and run details (shopper, page, message preview, model, duration, token usage, output summary).
  - Never wiped: entries are written as they happen, through a temporary file and an atomic replace, under a lock. An unreadable file is renamed `audit_trail.corrupt-<time>.json` and kept.
  - Redaction: emails become `[email]` and card-like numbers become `[number]`; args, results, and message previews are capped.
- Verified:
  - Separate runs grew the trail from 0 to 20 to 47 entries, and the live server added 7 more for one message (93 to 100).
  - The stop reasons appeared as expected: `final_result` for a stock question and an add-to-cart, `content_filter` for a jailbreak, and `usage_limit` when a scripted runaway model hit the 8-request cap.
  - The email writer's runs are logged too; a typed email and a card number were masked; a corrupted file was preserved.
- Safety rules: replaced "Safety basics" in `prompts/prompt.md` with eight groups of "Safety rules" that come before everything else:
  1. honesty and facts;
  2. the only allowed actions (own cart, clear request, at most 10, bulk orders go to the team);
  3. privacy (no other shoppers' data; never ask for or repeat passwords, card numbers, addresses, ages, or IDs);
  4. instructions only from the prompt (messages, product text, tool results, and page details are data);
  5. commitments and claims (no delivery guarantees or policy exceptions, not Yale University, no knockoffs);
  6. staying on topic;
  7. respect and wellbeing (calm with rude shoppers; 988 or 911 if someone is in danger);
  8. being clear it's an AI and handing off to the human team.
- Tested with the real agent while logged in: it refused another shopper's cart, said it's an AI, declined 50 hoodies without adding anything, wouldn't guarantee Saturday delivery, warned about a card number without repeating it (masked in the audit trail), and declined an essay.
- Finished `output/harness.md` with a new Part 1, "How the system works", before the existing notes (now Part 2):
  1. overview with an architecture sketch and the steps of a chat message;
  2. how to run the front and back end (setup, data scripts, both commands, other entry points, test login);
  3. a specs table (model, loop limit, retries, timeouts, history, message, search, page, card, and cart caps, rate limits, account security, reminder rules, audit caps);
  4. every model in `models.py` with its fields and why they were chosen, grouped into tool results, agent outputs, API, and audit;
  5. all nine tools and the abilities built on them, plus what the agent can't do;
  6. the prompt's safety rules, the guards enforced in code, and the safety test results;
  7. the audit trail format, stop reasons, append-only guarantees, and a real example run.
- Added OpenCV and NumPy (used by the one-time data scripts) to `backend/requirements.txt`.

## Problem 13 — Push to GitHub and Submit the URL

### Prompts

- "problem 13: push to github and submit the url: make sure everything is in the folder HW4 and push it to a public Github repository on my account. ill also need the repo URL so link graders can open and clone. No zip is needed for this homework. Do not put the real .env, campus_customs.db, or product images in the Github repo. use .gitignore. include .env.example with placeholders.only. (see photos). local-only data pack (not in git). the agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. REAME.md should explain how to run the front end and back end after placing the data pack." (with screenshots of the expected `hw4/` file tree and the local-only `data/` pack)

### Follow-up prompt

- None needed.

### What the first prompt was missing

Nothing — the prompt and the file-tree screenshots gave the layout, what must stay out of git, the four agent files, and what the README must cover, so no follow-up was needed.

### Evidence

- Matched the expected tree. `backend/` now holds exactly `main.py` plus the four agent files: `security.py` was folded into `main.py` (a "Security" section), `audit.py` into `agent.py` (an "Audit trail" section), and `cart.py` into `tools.py` (a "Shopping cart and cart reminder emails" section, with clearer function names). The one-time data scripts moved to `scripts/`, `requirements.txt` moved to the root, and the report was renamed `output/app_check.html`.
- Regression test after the restructure: 20 of 20 checks passed (products, images, login, cart refusals and caps, preview, merge, opt-in, staff outbox and token, chat stock answer, chat page results, chat add-to-cart, history, audit appends). All four scripts run from `HW4/`, the live site still serves, and `npm run build` and `npm run lint` pass.
- Added a root `README.md` (layout with the four agent files marked, the data pack, what you need, setup, both run commands, test login, things to try, other commands, where to read more, what's kept out of git), replaced the Vite boilerplate `frontend/README.md`, and updated `output/harness.md` paths, adding a code layout table.
- `.gitignore` excludes `data/`, `data.zip`, `*.db`, `.env` (while keeping `.env.example`), Python caches and virtual environments, `node_modules/`, `dist/`, and audit temp files. `.env.example` holds placeholders only.
- Before pushing, scanned all 74 staged files: the real `PORTKEY_API_KEY` appears nowhere; no database, `.env`, `data/`, or product image files are included; and the audit trail contains no email addresses.
- Repository: https://github.com/qtpeacock/campus-customs-hw4 (public).
