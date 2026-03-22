"use client";

import { useState } from "react";
import { signIn, signOut, useSession, SessionProvider } from "next-auth/react";

export default function Home() {
  return (
    <SessionProvider>
      <GitStoryDashboard />
    </SessionProvider>
  );
}

function GitStoryDashboard() {
  const { data: session }: any = useSession();
  const [publicUrl, setPublicUrl] = useState("");
  const [userRepos, setUserRepos] = useState<any[]>([]);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // --- FUNCTION: Fetch list of repos ---
  const fetchMyRepos = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/get-repos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: session.accessToken }),
      });
      const data = await res.json();
      setUserRepos(data.repos);
    } catch (error) {
      alert("Error fetching repos. Make sure Python server is running!");
    }
    setLoading(false);
  };

  // --- FUNCTION: Analyze a specific repo ---
  const analyzeRepo = async (target: string, isPrivate: boolean) => {
    setLoading(true);
    setResults(null); // Clear old results
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_target: target,
          token: session?.accessToken || null,
          is_private: isPrivate,
        }),
      });
      const data = await res.json();
      setResults(data);
    } catch (error) {
      alert("Analysis failed. Check Python terminal for errors.");
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "40px", fontFamily: "sans-serif" }}>
      <h1 style={{ textAlign: "center", fontSize: "2.5rem" }}>GitStory Data Gatherer ⛏️</h1>
      
      <div style={{ display: "flex", gap: "20px", marginTop: "40px" }}>
        
        {/* LEFT SIDE: Public Repos */}
        <div style={{ flex: 1, padding: "20px", border: "1px solid #ccc", borderRadius: "10px" }}>
          <h2>🌍 Public Repository</h2>
          <p style={{ fontSize: "14px", color: "gray" }}>Paste any public GitHub link here.</p>
          <input 
            type="text" 
            placeholder="e.g. ishepard/pydriller"
            value={publicUrl}
            onChange={(e) => setPublicUrl(e.target.value)}
            style={{ width: "100%", padding: "10px", margin: "10px 0", borderRadius: "5px", border: "1px solid gray" }}
          />
          <button 
            onClick={() => analyzeRepo(publicUrl, false)}
            style={{ width: "100%", padding: "10px", background: "blue", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}
          >
            Analyze Public Repo
          </button>
        </div>

        {/* RIGHT SIDE: Private Repos (Auth) */}
        <div style={{ flex: 1, padding: "20px", border: "1px solid #ccc", borderRadius: "10px" }}>
          <h2>🔒 Private Vault</h2>
          
          {!session ? (
            <div>
              <p style={{ fontSize: "14px", color: "gray" }}>Login to see your private code.</p>
              <button 
                onClick={() => signIn("github")}
                style={{ width: "100%", padding: "10px", background: "black", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}
              >
                Login with GitHub
              </button>
            </div>
          ) : (
            <div>
              <p>Logged in as: <strong>{session.user?.name}</strong></p>
              <button onClick={() => signOut()} style={{ fontSize: "12px", color: "red", background: "none", border: "none", cursor: "pointer", marginBottom: "15px" }}>(Logout)</button>
              
              <button 
                onClick={fetchMyRepos}
                style={{ width: "100%", padding: "10px", background: "green", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", marginBottom: "15px" }}
              >
                Fetch My Repositories
              </button>

              {/* Display user's repos as clickable buttons */}
              <div style={{ maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "5px" }}>
                {userRepos.map((repo, idx) => (
                  <button 
                    key={idx}
                    onClick={() => analyzeRepo(repo.name, repo.private)}
                    style={{ padding: "8px", textAlign: "left", background: "#f0f0f0", border: "1px solid #ddd", borderRadius: "4px", cursor: "pointer" }}
                  >
                    {repo.private ? "🔒" : "🌍"} {repo.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* BOTTOM SECTION: The Results Screen */}
      <div style={{ marginTop: "40px" }}>
        {loading && <h3 style={{ textAlign: "center", color: "blue" }}>⏳ Mining Data... Please wait...</h3>}
        
        {/* IF PYTHON SENDS AN ERROR, SHOW IT IN RED! */}
        {results && results.detail && (
          <div style={{ padding: "20px", background: "#ffe6e6", color: "#cc0000", borderRadius: "10px", border: "1px solid red" }}>
            <h3>❌ Python Server Error:</h3>
            <p>{results.detail}</p>
          </div>
        )}

        {/* IF PYTHON SENDS SUCCESS DATA, SHOW IT IN GREEN! */}
        {results && results.status === "Success" && (
          <div style={{ padding: "20px", background: "#1e1e1e", color: "#00ff00", borderRadius: "10px", overflowX: "auto" }}>
            <h3>📊 Extracted Data for: {results.repo_analyzed}</h3>
            <pre style={{ fontSize: "14px" }}>
              {JSON.stringify(results.data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}