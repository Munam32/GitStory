"use client";

import React from 'react';

interface Benchmark {
  title: string;
  description: string;
  nature: string;
  urgency: number;
  date: string;
  commit_hash?: string;
}

interface BenchmarkCardProps {
  benchmark: Benchmark;
  isLast: boolean;
  onHighlight?: () => void;
  isHighlighted?: boolean;
}

const natureColors: Record<string, string> = {
  feature: '#4ade80',
  refactor: '#60a5fa',
  fix: '#f87171',
  milestone: '#facc15',
  default: '#94a3b8'
};

const BenchmarkCard: React.FC<BenchmarkCardProps> = ({ benchmark, isLast, onHighlight, isHighlighted }) => {
  const color = natureColors[benchmark.nature.toLowerCase()] || natureColors.default;
  const dateStr = new Date(benchmark.date).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric'
  });

  return (
    <div className={`benchmark-row ${isHighlighted ? 'active' : ''}`} onClick={onHighlight}>
      <div className="dot-column">
        <div className="dot" style={{ backgroundColor: color }}></div>
        {!isLast && <div className="connector"></div>}
      </div>
      
      <div className="card-column">
        <div className={`card ${isHighlighted ? 'highlighted' : ''}`} style={{ borderColor: isHighlighted ? color : '#f1f5f9' }}>
          <div className="card-header">
            <span className="nature-tag" style={{ backgroundColor: color + '22', color }}>
              {benchmark.nature.toUpperCase()}
            </span>
            <span className="date-text">{dateStr}</span>
          </div>
          <h3 className="card-title">{benchmark.title}</h3>
          <p className="card-description">{benchmark.description}</p>
          <div className="urgency-bar">
            {[1, 2, 3, 4, 5].map(i => (
              <div 
                key={i} 
                className={`urgency-dot ${i <= benchmark.urgency ? 'active' : ''}`}
                style={{ backgroundColor: i <= benchmark.urgency ? color : '#e2e8f0' }}
              ></div>
            ))}
            <span className="urgency-label">Urgency</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .benchmark-row {
          display: flex;
          gap: 24px;
          margin-bottom: 24px;
          cursor: pointer;
        }
        .dot-column {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 20px;
        }
        .dot {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          border: 4px solid white;
          box-shadow: 0 0 0 2px #e2e8f0;
          z-index: 1;
          transition: transform 0.2s;
        }
        .benchmark-row:hover .dot {
          transform: scale(1.2);
        }
        .connector {
          width: 2px;
          flex-grow: 1;
          background: #e2e8f0;
          margin: 4px 0;
        }
        .card-column {
          flex-grow: 1;
          padding-bottom: 32px;
        }
        .card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          border: 1px solid #f1f5f9;
          transition: all 0.2s;
        }
        .card.highlighted {
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          transform: translateX(8px);
        }
        .card:hover {
          transform: translateY(-4px);
        }
        .card.highlighted:hover {
          transform: translateY(-4px) translateX(8px);
        }
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .nature-tag {
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .date-text {
          font-size: 0.85rem;
          color: #94a3b8;
        }
        .card-title {
          font-size: 1.25rem;
          font-weight: 700;
          margin-bottom: 8px;
          color: #1e293b;
        }
        .card-description {
          font-size: 0.95rem;
          color: #475569;
          line-height: 1.5;
          margin-bottom: 16px;
        }
        .urgency-bar {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .urgency-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .urgency-label {
          margin-left: 8px;
          font-size: 0.75rem;
          color: #94a3b8;
          text-transform: uppercase;
        }
      `}</style>
    </div>
  );
};

export default BenchmarkCard;
