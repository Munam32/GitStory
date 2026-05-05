"use client";

import React, { useState } from 'react';
import Timeline from '@/components/Timeline';
import Link from 'next/link';

export default function TimelinePage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFetchTimeline = async () => {
    if (!repoUrl) return;
    setLoading(true);
    setError('');
    setData(null);
    try {
      const response = await fetch(`http://localhost:8002/api/timeline?repo_url=${encodeURIComponent(repoUrl)}`);
      const result = await response.json();
      if (response.ok && result.narration && result.commits) {
        setData(result);
      } else {
        setError(result.detail || result.error || 'Failed to generate narration.');
      }
    } catch (err) {
      setError('Failed to connect to the backend API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <main>
        {!data ? (
          <div className="hero">
            <h1>Gitstory</h1>
            <p>Paste a GitHub URL to narrate your project's history.</p>
            <div className="input-group">
              <input 
                type="text" 
                placeholder="https://github.com/user/repo" 
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
              />
              <button onClick={handleFetchTimeline} disabled={loading}>
                {loading ? 'Analyzing...' : 'Generate Narration'}
              </button>
            </div>
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
              <Link href={`/hotzone?repo_url=${encodeURIComponent(repoUrl)}`} prefetch={false}>
                <button 
                  style={{ background: 'transparent', color: '#64748b', border: '1px solid #e2e8f0' }}
                  disabled={!repoUrl}
                >
                  View File Hotzone
                </button>
              </Link>
            </div>
            {error && <p className="error">{error}</p>}
          </div>
        ) : (
          <div style={{ width: '100%' }}>
            <nav className="nav">
              <div className="nav-content">
                <div className="logo" onClick={() => setData(null)}>Gitstory</div>
                <div className="nav-links">
                  <span className="active">Timeline</span>
                  <Link href={`/hotzone?repo_url=${encodeURIComponent(repoUrl)}`}>
                    <span>Hotzone</span>
                  </Link>
                </div>
              </div>
            </nav>
            <Timeline data={data} />
          </div>
        )}
      </main>

      <style jsx global>{`
        body {
          margin: 0;
          padding: 0;
          background: #fdfdfd;
        }
        .app-container {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
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
        .logo {
          font-weight: 800;
          font-size: 1.5rem;
          cursor: pointer;
        }
        .nav-links {
          display: flex;
          gap: 24px;
        }
        .nav-links span {
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
          transition: color 0.2s;
        }
        .nav-links span:hover, .nav-links span.active {
          color: #1e293b;
        }
        .hero {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 20px;
          text-align: center;
          margin-top: 100px;
        }
        .hero h1 {
          font-size: 4rem;
          margin-bottom: 10px;
          font-weight: 800;
          letter-spacing: -0.02em;
        }
        .hero p {
          font-size: 1.25rem;
          color: #64748b;
          margin-bottom: 30px;
        }
        .input-group {
          display: flex;
          gap: 12px;
          width: 100%;
          max-width: 600px;
        }
        input {
          flex: 1;
          padding: 16px 20px;
          border-radius: 12px;
          border: 2px solid #e2e8f0;
          font-size: 1rem;
          outline: none;
          transition: border-color 0.2s;
        }
        input:focus {
          border-color: #6366f1;
        }
        button {
          padding: 16px 32px;
          border-radius: 12px;
          background: #1e293b;
          color: white;
          font-weight: 700;
          border: none;
          cursor: pointer;
          transition: background 0.2s;
        }
        button:hover {
          background: #0f172a;
        }
        button:disabled {
          background: #94a3b8;
          cursor: not-allowed;
        }
        .error {
          color: #ef4444;
          margin-top: 20px;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
}
