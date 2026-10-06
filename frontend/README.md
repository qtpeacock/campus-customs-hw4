# Campus Customs front end

React + Vite + TypeScript site for Campus Customs. See the repository's main `README.md` for setup and how to run the front end together with the FastAPI back end.

```bash
npm install
npm run dev
```

The second command starts http://127.0.0.1:5173 and forwards `/api` and `/images` to the back end on port 8000. `npm run build` type-checks and builds, and `npm run lint` runs the linter.

Main folders in `src/`:
- `pages/` (Home, Products, Product, Cart, About, Log In, Create Account, staff Outbox)
- `components/` (nav, product cards, chat panel, carousel, gallery)
- `auth/`, `cart/`, `chat/` (shared state)
- `api.ts` (every backend call), `catalog.ts` (types, collections, sorting)
- `index.css` + `storefront.css` (styles)
