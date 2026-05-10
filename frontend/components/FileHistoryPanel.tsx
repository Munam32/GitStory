"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CommitHistory {
  hash: string;
  msg: string;
  author: string;
  date: string;
  insertions: number;
  deletions: number;
}

interface FileHistoryPanelProps {
  filePath: string | null;
  history: CommitHistory[];
  onClose: () => void;
  loading: boolean;
}

const FileHistoryPanel: React.FC<FileHistoryPanelProps> = ({ filePath, history, onClose, loading }) => {
  const safeHistory = Array.isArray(history) ? history : [];
  
  return (
    <AnimatePresence>
      {filePath && (
        <React.Fragment key="file-history-modal">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'black',
              zIndex: 2000,
            }}
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              width: '400px',
              height: '100%',
              backgroundColor: 'white',
              boxShadow: '-4px 0 15px rgba(0,0,0,0.1)',
              zIndex: 2001,
              display: 'flex',
              flexDirection: 'column',
              padding: '24px',
              overflowY: 'auto'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>File History</h2>
              <button 
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#64748b'
                }}
              >
                &times;
              </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#64748b', fontSize: '0.875rem', wordBreak: 'break-all' }}>{filePath}</p>
            </div>

            {loading ? (
              <p>Loading history...</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {safeHistory.map((commit) => (
                  <div 
                    key={commit.hash} 
                    style={{ 
                      padding: '16px', 
                      borderRadius: '12px', 
                      border: '1px solid #e2e8f0',
                      backgroundColor: '#f8fafc'
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>{commit.msg}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{commit.author}</span>
                      <span>{new Date(commit.date).toLocaleDateString()}</span>
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '0.75rem', display: 'flex', gap: '8px' }}>
                      <span style={{ color: '#22c55e' }}>+ {commit.insertions}</span>
                      <span style={{ color: '#ef4444' }}>- {commit.deletions}</span>
                      <span style={{ color: '#94a3b8', marginLeft: 'auto' }}>{commit.hash.substring(0, 7)}</span>
                    </div>
                  </div>
                ))}
                {safeHistory.length === 0 && <p>No history found.</p>}
              </div>
            )}
          </motion.div>
        </React.Fragment>
      )}
    </AnimatePresence>
  );
};

export default FileHistoryPanel;
