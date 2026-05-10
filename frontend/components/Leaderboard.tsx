import React from 'react';

// Define the exact shape of the data coming from Python
interface Contributor {
  name: string;
  commits: number;
  avatar_url: string;
}

interface LeaderboardProps {
  contributors: Contributor[];
}

export default function Leaderboard({ contributors }: LeaderboardProps) {
  if (!contributors || contributors.length === 0) {
    return <p className="text-gray-400 text-sm p-4">No contributors found.</p>;
  }

  // Find the highest commit count so we can scale the green progress bars perfectly
  const maxCommits = Math.max(...contributors.map(c => c.commits));
  const medals = ["🥇", "🥈", "🥉"];

  return (
    <div className="bg-gray-900 text-white p-6 rounded-xl shadow-2xl w-full max-w-lg border border-gray-800">
      <h2 className="text-2xl font-bold mb-6 border-b border-gray-700 pb-3 flex items-center gap-2">
        🏆 Top Contributors
      </h2>
      
      <ul className="space-y-5">
        {contributors.map((user, index) => (
          <li key={index} className="flex items-center justify-between">
            
            {/* Left Side: Medal, Avatar, and Name */}
            <div className="flex items-center gap-3 w-1/2">
              <span className="text-2xl w-8 text-center drop-shadow-md">
                {index < 3 ? medals[index] : <span className="text-gray-500 text-base font-mono">#{index + 1}</span>}
              </span>
              <img 
                src={user.avatar_url} 
                alt={`${user.name}'s avatar`} 
                className="w-10 h-10 rounded-full border-2 border-gray-700 shadow-sm"
              />
              <span className="font-semibold truncate text-sm">{user.name}</span>
            </div>
            
            {/* Middle: Visual Progress Bar */}
            <div className="w-1/3 bg-gray-800 rounded-full h-2 mx-4 relative overflow-hidden">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-1000 ease-out" 
                style={{ width: `${(user.commits / maxCommits) * 100}%` }}
              ></div>
            </div>

            {/* Right Side: Commit Count */}
            <div className="w-1/6 text-right font-mono text-green-400 font-bold text-sm">
              {user.commits}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}