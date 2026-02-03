import React from 'react';
import type { FactionStatus } from '../types/telemetry';

interface FactionTableProps {
  data: Record<string, FactionStatus>;
}

const formatLargeNum = (n: number) => {
    if (n >= 1_000_000_000) return `${(n/1_000_000_000).toFixed(1)}B`;
    if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n/1_000).toFixed(1)}K`;
    return Math.floor(n).toString();
};

export const FactionTable: React.FC<FactionTableProps> = ({ data }) => {
  // Filter out GLOBAL_ entries if any
  const factions = Object.entries(data).filter(([k]) => !k.startsWith('GLOBAL_'));
  const sortedFactions = factions.sort(([, a], [, b]) => b.Score - a.Score);

  return (
    <div className="bg-bg-card border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/50 flex justify-between items-center">
        <h3 className="font-semibold text-sm uppercase tracking-wider text-text-secondary">Faction Rankings</h3>
        <span className="text-xs text-gray-600">{sortedFactions.length} Active Factions</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-500 uppercase bg-gray-900/50">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Faction</th>
              <th className="px-4 py-3 text-right">Score</th>
              <th className="px-4 py-3 text-right text-gray-600" title="Systems">Sys</th>
              <th className="px-4 py-3 text-right text-gray-600" title="Planets">Pln</th>
              <th className="px-4 py-3 text-right text-gray-600" title="Fleets">Flt</th>
              <th className="px-4 py-3 text-right text-gray-600" title="Armies">Army</th>
              <th className="px-4 py-3 text-right" title="Requisition">Res</th>
              <th className="px-4 py-3 text-right" title="Tech Level">Tech</th>
              <th className="px-4 py-3 text-center">W / L / D</th>
              <th className="px-4 py-3 text-center">Posture</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {sortedFactions.map(([name, stats], idx) => {
              // Formatting name
              const displayName = name.replace(/_/g, ' ');
              const rankColor = idx < 3 ? 'text-yellow-500' : 'text-gray-400';

              // Calculate Losses
              const losses = stats.BF - stats.BW - stats.BD;

              return (
                <tr key={name} className="hover:bg-gray-800/30 transition-colors">
                  <td className={`px-4 py-3 font-mono ${rankColor}`}>{idx + 1}</td>
                  <td className="px-4 py-3 font-medium text-white">
                    <div className="flex items-center gap-2">
                        <span className="truncate max-w-[200px]" title={displayName}>{displayName}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-bold text-accent">{formatLargeNum(stats.Score)}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{stats.S}</td>
                  <td className="px-4 py-3 text-right text-gray-400">{stats.P}</td>
                  <td className="px-4 py-3 text-right text-cyan-400">{stats.F}</td>
                  <td className="px-4 py-3 text-right text-green-400">{stats.A}</td>
                  <td className="px-4 py-3 text-right font-mono text-yellow-600">{formatLargeNum(stats.R || stats.Req || 0)}</td>
                  <td className="px-4 py-3 text-right text-purple-400">{stats.T}</td>
                  <td className="px-4 py-3 text-center font-mono text-xs">
                    <span className="text-green-500">{stats.BW}</span>
                    <span className="text-gray-600 mx-1">/</span>
                    <span className="text-red-500">{losses < 0 ? 0 : losses}</span>
                    <span className="text-gray-600 mx-1">/</span>
                    <span className="text-gray-500">{stats.BD}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                        stats.Post?.includes('ATTACK') || stats.Post?.includes('BLITZ') ? 'bg-red-900/30 text-red-400' :
                        stats.Post?.includes('DEFEND') ? 'bg-blue-900/30 text-blue-400' :
                        stats.Post?.includes('EXPAND') ? 'bg-green-900/30 text-green-400' :
                        'bg-gray-800 text-gray-400'
                    }`}>
                        {stats.Post || 'IDLE'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
