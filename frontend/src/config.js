// ---------------------------------------------------------------------------
// Edit these to match your backend.
// ---------------------------------------------------------------------------

// The endpoint that receives the user's question.
// Expected request:  POST { query: string }
// Expected response: { answer: string }   (or { response: string })
export const API_URL = "http://127.0.0.1:5000/query";

// Messages cycled through while waiting for a response.
// Tweak these to reflect what your RAG pipeline is actually doing
// (retrieval, reranking, generation, etc.) if you want it to feel accurate.
export const WAITING_MESSAGES = [
  "Searching SEC filings…",
  "Pulling relevant context…",
  "Reasoning over the documents…",
  "Drafting your answer…",
];

// How often (ms) the waiting message rotates.
export const WAITING_MESSAGE_INTERVAL_MS = 2200;
