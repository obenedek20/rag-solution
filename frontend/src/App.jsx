import React, { useEffect, useRef, useState } from "react";
import {
  Theme,
  Header,
  HeaderName,
  Content,
  Grid,
  Column,
  TextArea,
  Button,
  Tile,
  InlineLoading,
  InlineNotification,
} from "@carbon/react";
import { Send } from "@carbon/icons-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { API_URL, WAITING_MESSAGES, WAITING_MESSAGE_INTERVAL_MS } from "./config.js";

export default function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [waitingIndex, setWaitingIndex] = useState(0);
  const intervalRef = useRef(null);

  // Cycle through waiting messages while a request is in flight.
  useEffect(() => {
    if (loading) {
      setWaitingIndex(0);
      intervalRef.current = setInterval(() => {
        setWaitingIndex((i) => (i + 1) % WAITING_MESSAGES.length);
      }, WAITING_MESSAGE_INTERVAL_MS);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [loading]);

  async function handleSubmit() {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });

      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      setAnswer(data.answer ?? data.response ?? JSON.stringify(data));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong reaching the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    // Enter submits, Shift+Enter adds a newline.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <Theme theme="g100">
      <Header aria-label="EDGAR Filings Assistant">
        <HeaderName href="#" prefix="">
          EDGAR Filings Assistant
        </HeaderName>
      </Header>

      <Content className="app-content">
        <Grid className="app-grid" fullWidth>
          <Column lg={8} md={6} sm={4} className="app-column">
            <Tile className="query-tile">
              <TextArea
                id="query-input"
                labelText="Ask a question about the filings"
                placeholder="e.g. What was Apple's R&D spend in FY2024?"
                rows={4}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <div className="submit-row">
                <Button
                  renderIcon={Send}
                  onClick={handleSubmit}
                  disabled={loading || !query.trim()}
                >
                  Ask
                </Button>
              </div>
            </Tile>

            {loading && (
              <Tile className="status-tile">
                <InlineLoading description={WAITING_MESSAGES[waitingIndex]} />
              </Tile>
            )}

            {error && (
              <InlineNotification
                kind="error"
                title="Request failed"
                subtitle={error}
                onCloseButtonClick={() => setError(null)}
                lowContrast
              />
            )}

            {answer && !loading && (
              <Tile className="answer-tile">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {answer}
                  </ReactMarkdown>
              </Tile>
            )}
          </Column>
        </Grid>
      </Content>
    </Theme>
  );
}
