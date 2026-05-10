"use client";

import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import BenchmarkCard from './BenchmarkCard';

interface Benchmark {
  title: string;
  description: string;
  nature: string;
  urgency: number;
  date: string;
  impact_score: number;
  commit_hash?: string;
}

interface Commit {
  hash: string;
  msg: string;
  author: string;
  date: string;
  insertions: number;
  deletions: number;
}

interface TimelineProps {
  data: {
    narration: {
      project_summary: string;
      benchmarks: Benchmark[];
    };
    commits: Commit[];
  };
}

const Timeline: React.FC<TimelineProps> = ({ data }) => {
  const [highlightedHash, setHighlightedHash] = useState<string | null>(null);

  const handleHighlight = (hash?: string) => {
    if (hash) {
      setHighlightedHash(hash);
      const element = document.getElementById(`commit-${hash}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  return (
    <div className="timeline-layout">
      <div className="timeline-content">
        <header className="timeline-header">
          <h1>Project Narration</h1>
          <p className="summary">{data.narration.project_summary}</p>
        </header>

        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.narration.benchmarks}>
              <defs>
                <linearGradient id="colorImpact" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" hide />
              <YAxis hide />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="impact_score" 
                stroke="#8884d8" 
                fillOpacity={1} 
                fill="url(#colorImpact)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="benchmarks-list">
          {data.narration.benchmarks.map((benchmark, index) => (
            <BenchmarkCard 
              key={index} 
              benchmark={benchmark} 
              isLast={index === data.narration.benchmarks.length - 1}
              onHighlight={() => handleHighlight(benchmark.commit_hash)}
              isHighlighted={benchmark.commit_hash === highlightedHash}
            />
          ))}
        </div>
      </div>

      <div className="commits-sidebar">
        <h3>Repository History</h3>
        <div className="commits-list">
          {data.commits.map((commit) => (
            <div 
              key={commit.hash} 
              id={`commit-${commit.hash}`}
              className={`commit-item ${highlightedHash === commit.hash ? 'highlighted' : ''}`}
            >
              <div className="commit-dot"></div>
              <div className="commit-info">
                <div className="commit-msg">{commit.msg}</div>
                <div className="commit-meta">
                  <span>{commit.author}</span>
                  <span>{new Date(commit.date).toLocaleDateString()}</span>
                </div>
                <div className="commit-hash">{commit.hash.substring(0, 7)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .timeline-layout {
          display: flex;
          max-width: 1400px;
          margin: 0 auto;
          gap: 40px;
          padding: 40px 20px;
        }
        .timeline-content {
          flex: 1;
          max-width: 800px;
        }
        .timeline-header {
          text-align: left;
          margin-bottom: 40px;
        }
        .timeline-header h1 {
          font-size: 2.5rem;
          font-weight: 800;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-fill-color: transparent;
          margin-bottom: 16px;
        }
        .summary {
          font-size: 1.1rem;
          color: #64748b;
          line-height: 1.6;
        }
        .chart-wrapper {
          margin-bottom: 60px;
          background: white;
          border-radius: 16px;
          padding: 20px;
          border: 1px solid #e2e8f0;
        }
        .benchmarks-list {
          position: relative;
        }
        .commits-sidebar {
          width: 350px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 24px;
          height: calc(100vh - 120px);
          position: sticky;
          top: 40px;
          display: flex;
          flex-direction: column;
        }
        .commits-sidebar h3 {
          margin-top: 0;
          margin-bottom: 20px;
          font-size: 1.1rem;
          font-weight: 700;
          color: #1e293b;
        }
        .commits-list {
          overflow-y: auto;
          flex: 1;
          padding-right: 8px;
        }
        .commit-item {
          display: flex;
          gap: 16px;
          padding: 12px;
          border-radius: 8px;
          transition: background 0.2s;
          position: relative;
          margin-bottom: 8px;
        }
        .commit-item.highlighted {
          background: #f1f5f9;
          box-shadow: 0 0 0 2px #6366f1;
        }
        .commit-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #cbd5e1;
          margin-top: 6px;
          flex-shrink: 0;
        }
        .commit-item.highlighted .commit-dot {
          background: #6366f1;
        }
        .commit-info {
          flex: 1;
          min-width: 0;
        }
        .commit-msg {
          font-size: 0.9rem;
          font-weight: 600;
          color: #334155;
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .commit-meta {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: #64748b;
        }
        .commit-hash {
          font-family: monospace;
          font-size: 0.7rem;
          color: #94a3b8;
          margin-top: 4px;
        }
      `}</style>
    </div>
  );
};

export default Timeline;
