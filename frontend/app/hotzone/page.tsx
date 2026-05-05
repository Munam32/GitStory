"use client";

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import HotzoneTreemap from '@/components/HotzoneTreemap';
import FileHistoryPanel from '@/components/FileHistoryPanel';
import Link from 'next/link';

function HotzoneContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const repo_url = searchParams.get('repo_url');
  
  const [url, setUrl] = useState('');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [selectedFile, setSelectedFile] = useState<any | null>(null);
  const [fileHistory, setFileHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (repo_url) {
      const decodedUrl = decodeURIComponent(repo_url as string);
      setUrl(decodedUrl);
      fetchHotzoneData(decodedUrl);
    }
  }, [repo_url]);

  const fetchHotzoneData = async (repoUrl: string) => {
    if (!repoUrl) return;
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`http://localhost:8002/api/hotzone?repo_url=${encodeURIComponent(repoUrl)}`);
      const result = await response.json();
      if (response.ok && Array.isArray(result)) {
        setData(result);
      } else {
        setError(result.detail || result.error || 'Failed to fetch hotzone data.');
      }
    } catch (err) {
      setError('Failed to fetch hotzone data.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (file: any) => {
    setSelectedFile(file);
    setHistoryLoading(true);
    try {
      const response = await fetch(`http://localhost:8002/api/file-history?repo_url=${encodeURIComponent(url)}&file_path=${encodeURIComponent(file.path)}`);
      const result = await response.json();
      if (response.ok && Array.isArray(result)) {
        setFileHistory(result);
      } else {
        setFileHistory([]);
      }
    } catch (err) {
      console.error('Failed to fetch file history');
    } finally {
      setHistoryLoading(false);
    }
  };

  return (
    <div className="hotzone-container">
      <nav className="nav">
        <div className="nav-content">
          <div className="logo" onClick={() => router.push('/')}>Gitstory</div>
          <div className="nav-links">
            <Link href="/timeline">
              <span>Timeline</span>
            </Link>
            <span className="active">Hotzone</span>
          </div>
        </div>
      </nav>

      <main>
        {!data.length && !loading ? (
          <div className="hero">
            <h1>File Hotzone</h1>
            <p>Identify high-churn files in your repository.</p>
            <div className="input-group">
              <input 
                type="text" 
                placeholder="https://github.com/user/repo" 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <button onClick={() => fetchHotzoneData(url)}>Analyze Hotzone</button>
            </div>
            {error && <p className="error">{error}</p>}
          </div>
        ) : (
          <div className="content">
            <div className="header">
              <h1>File Churn Hotzone</h1>
              <p>Files sized and colored by their churn score (accumulated additions + deletions).</p>
            </div>
            
            {loading ? (
              <div className="loading-state">Analyzing repository churn...</div>
            ) : (
              <HotzoneTreemap data={data} onFileClick={handleFileClick} />
            )}
          </div>
        )}
      </main>

      <FileHistoryPanel 
        filePath={selectedFile?.path} 
        history={fileHistory} 
        loading={historyLoading} 
        onClose={() => setSelectedFile(null)} 
      />

      <style jsx>{`
        .hotzone-container {
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
        main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 40px;
        }
        .hero {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding-top: 100px;
          text-align: center;
        }
        .hero h1 {
          font-size: 3rem;
          margin-bottom: 10px;
          font-weight: 800;
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
        }
        button {
          padding: 16px 32px;
          border-radius: 12px;
          background: #1e293b;
          color: white;
          font-weight: 700;
          border: none;
          cursor: pointer;
        }
        .header {
          margin-bottom: 32px;
        }
        .header h1 {
          font-size: 2rem;
          font-weight: 800;
          margin: 0 0 8px 0;
        }
        .header p {
          color: #64748b;
          margin: 0;
        }
        .loading-state {
          height: 400px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          color: #64748b;
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

export default function HotzonePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HotzoneContent />
    </Suspense>
  );
}
