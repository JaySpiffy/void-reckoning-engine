import React, { useState, useEffect } from 'react';
import { leaderboard, type LeaderboardEntry } from '../systems/LeaderboardService';

interface LeaderboardProps {
  gameMode?: 'survival' | 'simulation';
  limit?: number;
  showFilters?: boolean;
  onClose?: () => void;
  highlightPlayer?: string;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({
  gameMode,
  limit = 10,
  showFilters = true,
  onClose,
  highlightPlayer,
}) => {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'survival' | 'simulation'>('all');
  const [selectedEntry, setSelectedEntry] = useState<LeaderboardEntry | null>(null);
  const [stats, setStats] = useState({
    totalEntries: 0,
    averageScore: 0,
    highestScore: 0,
    uniquePlayers: 0,
  });

  useEffect(() => {
    const currentFilter = filter === 'all' ? undefined : filter;
    const currentGameMode = gameMode || currentFilter;
    
    setEntries(leaderboard.getEntries({ gameMode: currentGameMode, limit }));
    
    const stats = leaderboard.getStats(currentGameMode);
    setStats(stats);

    // Subscribe to updates
    return leaderboard.subscribe(() => {
      setEntries(leaderboard.getEntries({ gameMode: currentGameMode, limit }));
    });
  }, [filter, gameMode, limit]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };

  const formatScore = (score: number) => {
    return score.toLocaleString();
  };

  const getGameModeIcon = (mode: string) => {
    switch (mode) {
      case 'survival': return '🧬';
      case 'simulation': return '🤖';
      default: return '🎮';
    }
  };

  const getGameModeLabel = (mode: string) => {
    switch (mode) {
      case 'survival': return 'Survival';
      case 'simulation': return 'Simulation';
      default: return mode;
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.container} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>🏆 Leaderboard</h2>
          {onClose && (
            <button onClick={onClose} style={styles.closeButton}>×</button>
          )}
        </div>

        {/* Filters */}
        {showFilters && !gameMode && (
          <div style={styles.filters}>
            {(['all', 'survival', 'simulation'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={filter === f ? styles.activeFilter : styles.filterButton}
              >
                {f === 'all' ? 'All Games' : getGameModeIcon(f) + ' ' + getGameModeLabel(f)}
              </button>
            ))}
          </div>
        )}

        {/* Stats Summary */}
        <div style={styles.statsBar}>
          <div style={styles.statItem}>
            <span style={styles.statValue}>{stats.totalEntries}</span>
            <span style={styles.statLabel}>Total Scores</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statValue}>{formatScore(Math.round(stats.averageScore))}</span>
            <span style={styles.statLabel}>Average</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statValue}>{formatScore(stats.highestScore)}</span>
            <span style={styles.statLabel}>High Score</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statValue}>{stats.uniquePlayers}</span>
            <span style={styles.statLabel}>Players</span>
          </div>
        </div>

        {/* Table */}
        <div style={styles.tableContainer}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>#</th>
                <th style={styles.th}>Player</th>
                <th style={styles.th}>Score</th>
                <th style={styles.th}>Mode</th>
                <th style={styles.th}>Details</th>
                <th style={styles.th}>Date</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={6} style={styles.emptyState}>
                    No scores yet. Be the first!
                  </td>
                </tr>
              ) : (
                entries.map((entry, index) => (
                  <tr
                    key={entry.id}
                    style={{
                      ...styles.tr,
                      ...(highlightPlayer === entry.playerName ? styles.highlighted : {}),
                      ...(index === 0 ? styles.firstPlace : {}),
                      ...(index === 1 ? styles.secondPlace : {}),
                      ...(index === 2 ? styles.thirdPlace : {}),
                    }}
                    onClick={() => setSelectedEntry(entry)}
                  >
                    <td style={styles.td}>
                      {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                    </td>
                    <td style={{ ...styles.td, fontWeight: 'bold' }}>
                      {entry.playerName}
                    </td>
                    <td style={{ ...styles.td, ...styles.scoreCell }}>
                      {formatScore(entry.score)}
                    </td>
                    <td style={styles.td}>
                      <span style={styles.modeBadge}>
                        {getGameModeIcon(entry.gameMode)} {getGameModeLabel(entry.gameMode)}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <EntryDetails entry={entry} />
                    </td>
                    <td style={{ ...styles.td, fontSize: '12px', color: '#9ca3af' }}>
                      {formatDate(entry.metadata.date)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer Actions */}
        <div style={styles.footer}>
          <button
            onClick={() => {
              if (confirm('Clear all leaderboard data? This cannot be undone.')) {
                leaderboard.clearAll();
              }
            }}
            style={styles.clearButton}
          >
            Clear All
          </button>
          <button
            onClick={() => {
              const json = leaderboard.exportToJSON();
              const blob = new Blob([json], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `leaderboard-${Date.now()}.json`;
              a.click();
            }}
            style={styles.exportButton}
          >
            Export
          </button>
        </div>

        {/* Entry Detail Modal */}
        {selectedEntry && (
          <EntryDetailModal
            entry={selectedEntry}
            onClose={() => setSelectedEntry(null)}
          />
        )}
      </div>
    </div>
  );
};

// ===== SUB-COMPONENTS =====

const EntryDetails: React.FC<{ entry: LeaderboardEntry }> = ({ entry }) => {
  const { metadata } = entry;
  
  // Survival game data (primary)
  if (metadata.wavesSurvived) {
    return <span>Wave {metadata.wavesSurvived}</span>;
  }
  
  // Legacy football data (backward compatibility)
  if (metadata.teamName) {
    return <span>{metadata.teamName}</span>;
  }
  
  if (metadata.finalScore) {
    return <span>{metadata.finalScore}</span>;
  }
  
  if (metadata.touchdowns) {
    return <span>{metadata.touchdowns} TDs</span>;
  }
  
  return <span>-</span>;
};

const EntryDetailModal: React.FC<{
  entry: LeaderboardEntry;
  onClose: () => void;
}> = ({ entry, onClose }) => {
  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>
        <button onClick={onClose} style={styles.modalClose}>×</button>
        
        <h3 style={styles.modalTitle}>{entry.playerName}</h3>
        <div style={styles.modalScore}>{entry.score.toLocaleString()} points</div>
        
        <div style={styles.modalDetails}>
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Game Mode:</span>
            <span>{entry.gameMode}</span>
          </div>
          
          {entry.metadata.teamName && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Team:</span>
              <span>{entry.metadata.teamName}</span>
            </div>
          )}
          
          {entry.metadata.finalScore && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Final Score:</span>
              <span>{entry.metadata.finalScore}</span>
            </div>
          )}
          
          {entry.metadata.wavesSurvived && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Waves Survived:</span>
              <span>{entry.metadata.wavesSurvived}</span>
            </div>
          )}
          
          {entry.metadata.timeAlive && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Time Alive:</span>
              <span>{Math.round(entry.metadata.timeAlive / 60)}m {entry.metadata.timeAlive % 60}s</span>
            </div>
          )}
          
          {entry.metadata.touchdowns !== undefined && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Touchdowns:</span>
              <span>{entry.metadata.touchdowns}</span>
            </div>
          )}
          
          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Date:</span>
            <span>{new Date(entry.metadata.date).toLocaleString()}</span>
          </div>
        </div>
        
        <button onClick={onClose} style={styles.modalButton}>Close</button>
      </div>
    </div>
  );
};

// ===== STYLES =====

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  container: {
    background: '#1f2937',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '800px',
    maxHeight: '90vh',
    overflow: 'auto',
    padding: '24px',
    color: 'white',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    margin: 0,
    fontSize: '28px',
    background: 'linear-gradient(to right, #fbbf24, #f59e0b)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    color: '#9ca3af',
    fontSize: '32px',
    cursor: 'pointer',
    padding: '0',
    width: '40px',
    height: '40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  filters: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  filterButton: {
    padding: '8px 16px',
    background: '#374151',
    border: 'none',
    borderRadius: '8px',
    color: '#9ca3af',
    cursor: 'pointer',
    fontSize: '14px',
  },
  activeFilter: {
    padding: '8px 16px',
    background: '#3b82f6',
    border: 'none',
    borderRadius: '8px',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  statsBar: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '12px',
    marginBottom: '20px',
    padding: '16px',
    background: '#111827',
    borderRadius: '12px',
  },
  statItem: {
    textAlign: 'center',
  },
  statValue: {
    display: 'block',
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#3b82f6',
  },
  statLabel: {
    fontSize: '12px',
    color: '#9ca3af',
    textTransform: 'uppercase',
  },
  tableContainer: {
    overflow: 'auto',
    marginBottom: '16px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    borderBottom: '2px solid #374151',
    color: '#9ca3af',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    fontSize: '12px',
  },
  tr: {
    borderBottom: '1px solid #374151',
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  highlighted: {
    background: 'rgba(59, 130, 246, 0.2)',
  },
  firstPlace: {
    background: 'rgba(251, 191, 36, 0.1)',
  },
  secondPlace: {
    background: 'rgba(156, 163, 175, 0.1)',
  },
  thirdPlace: {
    background: 'rgba(251, 146, 60, 0.1)',
  },
  td: {
    padding: '12px',
    verticalAlign: 'middle',
  },
  scoreCell: {
    fontFamily: 'monospace',
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#22c55e',
  },
  modeBadge: {
    padding: '4px 8px',
    background: '#374151',
    borderRadius: '4px',
    fontSize: '12px',
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px',
    color: '#6b7280',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    paddingTop: '16px',
    borderTop: '1px solid #374151',
  },
  clearButton: {
    padding: '8px 16px',
    background: 'transparent',
    border: '1px solid #ef4444',
    borderRadius: '6px',
    color: '#ef4444',
    cursor: 'pointer',
    fontSize: '14px',
  },
  exportButton: {
    padding: '8px 16px',
    background: '#374151',
    border: 'none',
    borderRadius: '6px',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1001,
  },
  modal: {
    background: '#1f2937',
    borderRadius: '16px',
    padding: '24px',
    width: '100%',
    maxWidth: '400px',
    position: 'relative',
  },
  modalClose: {
    position: 'absolute',
    top: '16px',
    right: '16px',
    background: 'none',
    border: 'none',
    color: '#9ca3af',
    fontSize: '24px',
    cursor: 'pointer',
  },
  modalTitle: {
    margin: '0 0 8px 0',
    fontSize: '24px',
  },
  modalScore: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#fbbf24',
    marginBottom: '20px',
  },
  modalDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginBottom: '20px',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid #374151',
  },
  detailLabel: {
    color: '#9ca3af',
  },
  modalButton: {
    width: '100%',
    padding: '12px',
    background: '#3b82f6',
    border: 'none',
    borderRadius: '8px',
    color: 'white',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default Leaderboard;
