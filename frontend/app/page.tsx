"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { signIn, signOut, useSession, SessionProvider } from "next-auth/react";
import Link from "next/link";

const API = "http://localhost:8000";

export default function Home() {
  return (
    <SessionProvider>
      <GitStoryDashboard />
    </SessionProvider>
  );
}

// ─── Types ────────────────────────────────────────────────────────────────────

type Repo = { name: string; private: boolean };
type Message = { role: "user" | "assistant"; content: string };

// ─── Main Dashboard ───────────────────────────────────────────────────────────

function GitStoryDashboard() {
  const { data: session }: any = useSession();

  // Analyse panel state
  const [publicUrl, setPublicUrl] = useState("");
  const [userRepos, setUserRepos] = useState<Repo[]>([]);
  const [analyzeResults, setAnalyzeResults] = useState<any>(null);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);

  // Index panel state
  const [indexUrl, setIndexUrl] = useState("");
  const [indexJobId, setIndexJobId] = useState<string | null>(null);
  const [indexStatus, setIndexStatus] = useState<string>("");
  const [indexedRepos, setIndexedRepos] = useState<string[]>([]);
  const [indexLoading, setIndexLoading] = useState(false);

  // Chat panel state
  const [selectedRepo, setSelectedRepo] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // ── Fetch indexed repos on mount ──────────────────────────────────────────
  const refreshIndexedRepos = useCallback(async () => {
    try {
      const res = await fetch(`${API}/indexed-repos`);
      const data = await res.json();
      setIndexedRepos(data.repos ?? []);
    } catch {
      // server not running yet — ignore
    }
  }, []);

  useEffect(() => { refreshIndexedRepos(); }, [refreshIndexedRepos]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Poll index job status ─────────────────────────────────────────────────
  useEffect(() => {
    if (!indexJobId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/index-repo/status/${indexJobId}`);
        const data = await res.json();
        setIndexStatus(data.status);
        if (data.status === "done") {
          clearInterval(interval);
          setIndexJobId(null);
          setIndexLoading(false);
          setIndexStatus("");
          refreshIndexedRepos();
          alert(`Repo '${data.repo_name}' has been indexed! You can now chat with it.`);
        } else if (data.status === "error") {
          clearInterval(interval);
          setIndexJobId(null);
          setIndexLoading(false);
          setIndexStatus("");
          alert(`Indexing failed: ${data.error}`);
        }
      } catch {
        clearInterval(interval);
        setIndexLoading(false);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [indexJobId, refreshIndexedRepos]);

  // ── API Helpers ───────────────────────────────────────────────────────────

  const fetchMyRepos = async () => {
    setAnalyzeLoading(true);
    try {
      const res = await fetch(`${API}/get-repos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: session.accessToken }),
      });
      const data = await res.json();
      setUserRepos(data.repos ?? []);
    } catch {
      alert("Error fetching repos. Is the Python server running?");
    }
    setAnalyzeLoading(false);
  };

  const analyzeRepo = async (target: string, isPrivate: boolean) => {
    setAnalyzeLoading(true);
    setAnalyzeResults(null);
    try {
      const res = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_target: target,
          token: session?.accessToken ?? null,
          is_private: isPrivate,
        }),
      });
      const data = await res.json();
      setAnalyzeResults(data);
    } catch {
      alert("Analysis failed. Check the Python terminal for errors.");
    }
    setAnalyzeLoading(false);
  };

  const startIndexing = async () => {
    if (!indexUrl.trim()) return alert("Enter a GitHub URL to index.");
    setIndexLoading(true);
    setIndexStatus("pending");
    try {
      const res = await fetch(`${API}/index-repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: indexUrl.trim(),
          token: session?.accessToken ?? null,
          is_private: false,
        }),
      });
      const data = await res.json();
      setIndexJobId(data.job_id);
    } catch {
      alert("Failed to start indexing.");
      setIndexLoading(false);
      setIndexStatus("");
    }
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || !selectedRepo) return;
    const userMsg = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatLoading(true);

    // Add a placeholder assistant message we'll stream into
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, repo_name: selectedRepo }),
      });

      if (!res.ok) {
        const err = await res.json();
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: `Error: ${err.detail}`,
          };
          return updated;
        });
        setChatLoading(false);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by "\n\n"
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          if (payload === "[DONE]") break;
          try {
            const parsed = JSON.parse(payload);
            if (parsed.token) {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: updated[updated.length - 1].content + parsed.token,
                };
                return updated;
              });
            }
          } catch {
            // malformed chunk — skip
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Network error — is the Python server running?",
        };
        return updated;
      });
    }

    setChatLoading(false);
  };

  const resetChat = async () => {
    if (!selectedRepo) return;
    await fetch(`${API}/chat/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_name: selectedRepo }),
    });
    setMessages([]);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={styles.page}>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginBottom: '20px' }}>
        <Link href="/" style={{ fontWeight: 700, color: '#2563eb' }}>Dashboard</Link>
        <Link href="/timeline" style={{ color: '#6b7280' }}>Timeline</Link>
        <Link href="/hotzone" style={{ color: '#6b7280' }}>Hotzone</Link>
        <Link href="/review" style={{ color: '#6b7280' }}>Review</Link>
      </div>

      <h1 style={styles.title}>GitStory</h1>
      <p style={styles.subtitle}>Mine, Index, and Chat with any GitHub Repository</p>

      {/* ── Row 1: Analyse + Private Vault ─────────────────────────────── */}
      <div style={styles.row}>
        {/* Analyse Panel */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Analyse Repo</h2>
          <p style={styles.hint}>Surface-level stats via PyGithub + PyDriller</p>
          <input
            style={styles.input}
            type="text"
            placeholder="https://github.com/owner/repo"
            value={publicUrl}
            onChange={(e) => setPublicUrl(e.target.value)}
          />
          <button
            style={{ ...styles.btn, background: "#2563eb" }}
            onClick={() => analyzeRepo(publicUrl, false)}
            disabled={analyzeLoading}
          >
            {analyzeLoading ? "Analysing..." : "Analyse Public Repo"}
          </button>

          {!session ? (
            <button
              style={{ ...styles.btn, background: "#111", marginTop: 8 }}
              onClick={() => signIn("github")}
            >
              Login with GitHub for Private Repos
            </button>
          ) : (
            <>
              <p style={{ margin: "8px 0 4px", fontSize: 13 }}>
                Logged in as <strong>{session.user?.name}</strong>{" "}
                <span
                  style={{ color: "red", cursor: "pointer", fontSize: 12 }}
                  onClick={() => signOut()}
                >
                  (logout)
                </span>
              </p>
              <button
                style={{ ...styles.btn, background: "#16a34a" }}
                onClick={fetchMyRepos}
                disabled={analyzeLoading}
              >
                Fetch My Repos
              </button>
              <div style={styles.repoList}>
                {userRepos.map((r, i) => (
                  <button
                    key={i}
                    style={styles.repoItem}
                    onClick={() => analyzeRepo(r.name, r.private)}
                  >
                    {r.private ? "🔒" : "🌍"} {r.name}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Index Panel */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Index Repo for RAG</h2>
          <p style={styles.hint}>
            Clones, summarises, chunks, and embeds a repo into ChromaDB so you can chat with it.
          </p>
          <input
            style={styles.input}
            type="text"
            placeholder="https://github.com/owner/repo"
            value={indexUrl}
            onChange={(e) => setIndexUrl(e.target.value)}
          />
          <button
            style={{ ...styles.btn, background: "#7c3aed" }}
            onClick={startIndexing}
            disabled={indexLoading}
          >
            {indexLoading
              ? `Indexing... (${indexStatus})`
              : "Start Indexing"}
          </button>

          {indexedRepos.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <p style={{ fontSize: 13, fontWeight: 600, margin: "0 0 6px" }}>
                Already indexed:
              </p>
              <div style={styles.repoList}>
                {indexedRepos.map((r) => (
                  <button
                    key={r}
                    style={{
                      ...styles.repoItem,
                      background: selectedRepo === r ? "#ddd6fe" : "#f3f4f6",
                      fontWeight: selectedRepo === r ? 700 : 400,
                    }}
                    onClick={() => setSelectedRepo(r)}
                  >
                    🗂 {r}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Analyse Results ──────────────────────────────────────────────── */}
      {analyzeResults && (
        <div style={{ marginTop: 24 }}>
          {analyzeResults.detail ? (
            <div style={styles.errorBox}>
              <strong>Error:</strong> {analyzeResults.detail}
            </div>
          ) : (
            <AnalyzeResults data={analyzeResults} />
          )}
        </div>
      )}

      {/* ── Chat Panel ──────────────────────────────────────────────────── */}
      <div style={{ ...styles.card, marginTop: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={styles.cardTitle}>
            Chat with Repo{selectedRepo ? `: ${selectedRepo}` : ""}
          </h2>
          {selectedRepo && (
            <button style={styles.ghostBtn} onClick={resetChat}>
              Clear history
            </button>
          )}
        </div>

        {!selectedRepo ? (
          <p style={{ color: "#6b7280", fontSize: 14 }}>
            Index a repo above, then click its name to select it for chat.
          </p>
        ) : (
          <>
            <div style={styles.chatWindow}>
              {messages.length === 0 && (
                <p style={{ color: "#9ca3af", fontSize: 14, margin: "auto" }}>
                  Ask anything about <strong>{selectedRepo}</strong>...
                </p>
              )}
              {messages.map((m, i) => (
                <ChatBubble key={i} role={m.role} content={m.content} />
              ))}
              <div ref={chatBottomRef} />
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <input
                style={{ ...styles.input, flex: 1, margin: 0 }}
                type="text"
                placeholder="Ask about the codebase..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !chatLoading && sendMessage()}
                disabled={chatLoading}
              />
              <button
                style={{ ...styles.btn, width: "auto", padding: "0 20px", margin: 0 }}
                onClick={sendMessage}
                disabled={chatLoading || !chatInput.trim()}
              >
                {chatLoading ? "..." : "Send"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 12,
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "10px 14px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser ? "#2563eb" : "#f3f4f6",
          color: isUser ? "#fff" : "#111",
          fontSize: 14,
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {content || <span style={{ opacity: 0.4 }}>▌</span>}
      </div>
    </div>
  );
}

function AnalyzeResults({ data }: { data: any }) {
  const d = data.data;
  const langs = Object.entries(d.languages ?? {}) as [string, number][];
  const totalBytes = langs.reduce((s, [, v]) => s + v, 0);
  const contributors = Object.entries(d.top_contributors ?? {}) as [string, number][];
  const hotfiles = Object.entries(d.file_hotzones ?? {})
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 5) as [string, number][];

  return (
    <div style={{ ...styles.card, background: "#0f172a", color: "#e2e8f0" }}>
      <h3 style={{ margin: "0 0 16px", fontSize: 18 }}>
        Analysis: <span style={{ color: "#818cf8" }}>{data.repo_analyzed}</span>
      </h3>

      <div style={styles.statsGrid}>
        {/* Languages */}
        <div>
          <p style={styles.statLabel}>Languages</p>
          {langs.map(([lang, bytes]) => (
            <div key={lang} style={{ marginBottom: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                <span>{lang}</span>
                <span>{((bytes / totalBytes) * 100).toFixed(1)}%</span>
              </div>
              <div style={{ height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${(bytes / totalBytes) * 100}%`,
                    background: "#818cf8",
                    borderRadius: 2,
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Contributors */}
        <div>
          <p style={styles.statLabel}>Top Contributors</p>
          {contributors.sort(([,a],[,b]) => b-a).slice(0,5).map(([name, count]) => (
            <div key={name} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
              <span>{name}</span>
              <span style={{ color: "#a5b4fc" }}>{count} commits</span>
            </div>
          ))}
        </div>

        {/* Hotfiles */}
        <div>
          <p style={styles.statLabel}>Hottest Files</p>
          {hotfiles.map(([file, count]) => (
            <div key={file} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
              <span style={{ color: "#94a3b8", fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "70%" }}>{file}</span>
              <span style={{ color: "#f97316" }}>{count}x</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent commits */}
      <p style={{ ...styles.statLabel, marginTop: 16 }}>Recent Commits</p>
      {(d.recent_commits ?? []).slice(0, 5).map((c: any, i: number) => (
        <div key={i} style={{ borderLeft: "2px solid #334155", paddingLeft: 10, marginBottom: 8 }}>
          <p style={{ margin: 0, fontSize: 13, color: "#e2e8f0" }}>{c.message}</p>
          <p style={{ margin: 0, fontSize: 11, color: "#64748b" }}>{c.author} · {c.date?.slice(0, 10)}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "40px 20px",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  title: {
    textAlign: "center",
    fontSize: "2.4rem",
    fontWeight: 700,
    margin: 0,
  },
  subtitle: {
    textAlign: "center",
    color: "#6b7280",
    marginTop: 6,
    marginBottom: 32,
  },
  row: {
    display: "flex",
    gap: 20,
  },
  card: {
    flex: 1,
    padding: 20,
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    background: "#fff",
  },
  cardTitle: {
    margin: "0 0 4px",
    fontSize: 17,
    fontWeight: 600,
  },
  hint: {
    fontSize: 13,
    color: "#6b7280",
    margin: "0 0 12px",
  },
  input: {
    width: "100%",
    padding: "9px 12px",
    marginBottom: 8,
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontSize: 14,
    boxSizing: "border-box" as const,
  },
  btn: {
    width: "100%",
    padding: "10px 0",
    border: "none",
    borderRadius: 6,
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: 4,
  },
  ghostBtn: {
    background: "none",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    padding: "4px 10px",
    fontSize: 13,
    cursor: "pointer",
    color: "#374151",
  },
  repoList: {
    maxHeight: 180,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 4,
    marginTop: 8,
  },
  repoItem: {
    padding: "7px 10px",
    textAlign: "left",
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
  },
  chatWindow: {
    height: 400,
    overflowY: "auto",
    background: "#f9fafb",
    borderRadius: 8,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    border: "1px solid #e5e7eb",
  },
  errorBox: {
    padding: 16,
    background: "#fef2f2",
    border: "1px solid #fca5a5",
    borderRadius: 8,
    color: "#991b1b",
    fontSize: 14,
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 20,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    color: "#64748b",
    marginBottom: 8,
    marginTop: 0,
  },
};
