# EDGAR Filings Assistant — Frontend

A small Carbon Design System (IBM) frontend: a question box that sends a
query to your RAG backend and shows rotating "waiting" messages while it's
thinking, then displays the answer.

## Setup

```bash
npm install
npm run dev
```

This starts a dev server (default: http://localhost:5173).

## Connecting your backend

Edit `src/config.js`:

```js
export const API_URL = "http://localhost:8000/api/query";
```

The frontend sends:

```json
POST { "query": "<user's question>" }
```

and expects back:

```json
{ "answer": "<text>" }
```

(`response` is also accepted as a key, as a fallback.) If your backend's
request/response shape differs, adjust the `fetch` call and the
`data.answer ?? data.response ?? ...` line in `src/App.jsx`.

If your backend lives on a different origin, you'll need to enable CORS on
the backend (e.g. `flask-cors` / `fastapi.middleware.cors`) since the browser
will block the request otherwise.

## Customizing the waiting messages

Also in `src/config.js`:

```js
export const WAITING_MESSAGES = [
  "Searching SEC filings…",
  "Pulling relevant context…",
  "Reasoning over the documents…",
  "Drafting your answer…",
];
export const WAITING_MESSAGE_INTERVAL_MS = 2200;
```

These rotate automatically while a request is in flight (`InlineLoading` from
Carbon). Swap them out for messages that reflect your actual pipeline stages
if you want it to feel more accurate (e.g. "Re-ranking chunks…", "Calling
the LLM…").

## Structure

```
src/
  config.js     # backend URL + waiting messages (the file you'll edit most)
  App.jsx       # the whole UI (input, loading state, answer, errors)
  main.jsx      # React entry point
  index.scss    # imports Carbon's styles + a few layout tweaks
```

## Build for production

```bash
npm run build
npm run preview   # serve the built dist/ folder locally to sanity-check it
```

## Notes

- Theme is set to Carbon's dark theme (`g100`) in `App.jsx`. Change
  `<Theme theme="g100">` to `"white"`, `"g10"`, or `"g90"` for other Carbon
  themes.
- Enter submits the question; Shift+Enter adds a newline in the text box.
- Errors from the backend (non-2xx response, network failure, etc.) show as
  a dismissible Carbon `InlineNotification` rather than crashing the page.
