"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function ReviewPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [token, setToken] = useState('');
  const [commitCount, setCommitCount] = useState(1);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleReview = async () => {
    if (!repoUrl || !token) return alert('Repo URL and GitHub Token are required.');
    setLoading(true);
    setError('');
    setData(null);
    try {
      const response = await fetch(`http://localhost:8002/api/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl,
          github_token: token,
          commit_count: commitCount
        })
      });
      const result = await response.json();
      if (response.status !== 200) {
        setError(result.detail || 'Failed to generate review.');
      } else {
        setData(result);
      }
    } catch (err) {
      setError('Failed to connect to the backend API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="review-container">
      <nav className="nav">
        <div className="nav-content">
          <div className="logo"><Link href="/">Gitstory</Link></div>
          <div className="nav-links">
            <Link href="/timeline"><span>Timeline</span></Link>
            <Link href="/hotzone"><span>Hotzone</span></Link>
            <span className="active">Code Review</span>
          </div>
        </div>
      </nav>

      <main>
        <div className="hero">
          <h1>AI Code Review</h1>
          <p>Get automated AI feedback on your latest commits.</p>
          
          <div className="form-card">
            <div className="input-field">
              <label>Repository URL</label>
              <input 
                type="text" 
                placeholder="https://github.com/user/repo" 
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
              />
            </div>
            <div className="input-field">
              <label>GitHub Token</label>
              <input 
                type="password" 
                placeholder="ghp_xxxxxxxxxxxx" 
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
            </div>
            <div className="input-field">
              <label>Commits to Review (1-5)</label>
              <input 
                type="number" 
                min="1" 
                max="5"
                value={commitCount}
                onChange={(e) => setCommitCount(parseInt(e.target.value))}
              />
            </div>
            <button onClick={handleReview} disabled={loading}>
              {loading ? 'Reviewing...' : 'Generate AI Review'}
            </button>
            {error && <p className="error">{error}</p>}
          </div>
        </div>

        {data && (
          <div className="results">
            <h2>Review Results</h2>
            <div className="health-score">
              Health Score: <strong>{data.health_score}/100</strong>
            </div>
            <div className="review-content">
              <pre>{data.review}</pre>
            </div>
            {Array.isArray(data.files_analyzed) && data.files_analyzed.length > 0 && (
              <div className="files-list">
                <h3>Files Analyzed ({data.files_analyzed.length}):</h3>
                <ul>
                  {data.files_analyzed.map((f: string, i: number) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </main>

      <style jsx>{`
        .review-container {
          min-height: 100vh;
          background: #fdfdfd;
        }
        .nav {
          height: 64px;
          border-bottom: 1px solid #e2e8f0;
          display: flex;
          align-items: center;
          padding: 0 40px;
          background: white;
        }
        .nav-content {
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .logo a {
          font-weight: 800;
          font-size: 1.5rem;
          color: black;
          text-decoration: none;
        }
        .nav-links {
          display: flex;
          gap: 24px;
        }
        .nav-links span {
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
        }
        .nav-links span.active {
          color: #1e293b;
        }
        main {
          max-width: 800px;
          margin: 0 auto;
          padding: 40px 20px;
        }
        .hero {
          text-align: center;
          margin-bottom: 40px;
        }
        .hero h1 {
          font-size: 2.5rem;
          font-weight: 800;
          margin-bottom: 10px;
        }
        .hero p {
          color: #64748b;
          margin-bottom: 30px;
        }
        .form-card {
          background: white;
          padding: 30px;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
          text-align: left;
        }
        .input-field {
          margin-bottom: 20px;
        }
        .input-field label {
          display: block;
          font-size: 0.875rem;
          font-weight: 600;
          margin-bottom: 6px;
          color: #475569;
        }
        input {
          width: 100%;
          padding: 12px 16px;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
          font-size: 1rem;
          box-sizing: border-box;
        }
        button {
          width: 100%;
          padding: 14px;
          border-radius: 8px;
          background: #1e293b;
          color: white;
          font-weight: 700;
          border: none;
          cursor: pointer;
          font-size: 1rem;
        }
        button:disabled {
          background: #94a3b8;
        }
        .results {
          margin-top: 40px;
        }
        .health-score {
          font-size: 1.25rem;
          margin-bottom: 16px;
          padding: 12px;
          background: #f1f5f9;
          border-radius: 8px;
          border-left: 4px solid #1e293b;
        }
        .review-content {
          background: #0f172a;
          color: #e2e8f0;
          padding: 24px;
          border-radius: 12px;
          font-family: monospace;
          white-space: pre-wrap;
          font-size: 0.9rem;
          line-height: 1.5;
          overflow-x: auto;
        }
        .files-list {
          margin-top: 20px;
          font-size: 0.9rem;
          color: #64748b;
        }
        .error {
          color: #ef4444;
          margin-top: 10px;
          font-weight: 600;
          text-align: center;
        }
      `}</style>
    </div>
  );
}
