import React, { useState, useEffect, useRef } from 'react';
import { leaderboard } from '../systems/LeaderboardService';

interface NameEntryModalProps {
  score: number;
  gameMode: 'survival' | 'simulation';
  metadata?: {
    // Legacy fields (kept for backward compatibility)
    teamName?: string;
    finalScore?: string;
    wavesSurvived?: number;
    timeAlive?: number;
    // Legacy field from football game
touchdowns?: number;
  };
  onSubmit: (playerName: string) => void;
  onSkip: () => void;
  isHighScore?: boolean;
  rank?: number;
}

export const NameEntryModal: React.FC<NameEntryModalProps> = ({
  score,
  gameMode,
  metadata,
  onSubmit,
  onSkip,
  isHighScore: propIsHighScore,
  rank: propRank,
}) => {
  const [playerName, setPlayerName] = useState('');
  const [isHighScore, setIsHighScore] = useState(propIsHighScore ?? false);
  const [rank, setRank] = useState(propRank);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check if this is a high score on mount
  useEffect(() => {
    if (propIsHighScore === undefined) {
      const entries = leaderboard.getEntries({ gameMode, limit: 10 });
      const isHigh = entries.length < 10 || score > (entries[entries.length - 1]?.score || 0);
      setIsHighScore(isHigh);
      
      if (isHigh) {
        const playerRank = entries.filter(e => e.score > score).length + 1;
        setRank(playerRank);
      }
    }
  }, [score, gameMode, propIsHighScore]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!playerName.trim()) return;
    
    setIsSubmitting(true);
    
    // Add to leaderboard
    leaderboard.addEntry({
      playerName: playerName.trim(),
      score,
      gameMode,
      metadata: metadata || {},
    });
    
    onSubmit(playerName.trim());
  };

  const getGameModeTitle = () => {
    switch (gameMode) {
      case 'survival': return '🧬 You Died!';
      case 'simulation': return '🤖 Simulation Complete!';
      default: return '🎮 Game Over!';
    }
  };

  const getEncouragement = () => {
    if (rank === 1) return '🏆 NEW HIGH SCORE! You are the champion!';
    if (rank && rank <= 3) return `🥉 Top ${rank}! Amazing performance!`;
    if (isHighScore) return `✨ You made it to #${rank} on the leaderboard!`;
    return 'Good game! Try again to beat your score.';
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>{getGameModeTitle()}</h2>
          <div style={styles.scoreDisplay}>
            <span style={styles.scoreLabel}>Final Score</span>
            <span style={styles.scoreValue}>{score.toLocaleString()}</span>
          </div>
        </div>

        {/* Encouragement */}
        <div style={styles.encouragement}>
          {getEncouragement()}
        </div>

        {/* Stats Summary */}
        {metadata && (
          <div style={styles.statsGrid}>
            {/* Survival game stats (primary) */}
            {metadata.wavesSurvived !== undefined && (
              <div style={styles.statBox}>
                <span style={styles.statLabel}>Waves Survived</span>
                <span style={styles.statValue}>{metadata.wavesSurvived}</span>
              </div>
            )}
            {metadata.timeAlive && (
              <div style={styles.statBox}>
                <span style={styles.statLabel}>Time Alive</span>
                <span style={styles.statValue}>
                  {Math.floor(metadata.timeAlive / 60)}m {metadata.timeAlive % 60}s
                </span>
              </div>
            )}
            {/* Legacy football stats (backward compatibility) */}
            {metadata.teamName && (
              <div style={styles.statBox}>
                <span style={styles.statLabel}>Team</span>
                <span style={styles.statValue}>{metadata.teamName}</span>
              </div>
            )}
            {metadata.finalScore && (
              <div style={styles.statBox}>
                <span style={styles.statLabel}>Result</span>
                <span style={styles.statValue}>{metadata.finalScore}</span>
              </div>
            )}
            {metadata.touchdowns !== undefined && (
              <div style={styles.statBox}>
                <span style={styles.statLabel}>Touchdowns</span>
                <span style={styles.statValue}>{metadata.touchdowns}</span>
              </div>
            )}
          </div>
        )}

        {/* Name Entry Form */}
        {isHighScore ? (
          <form onSubmit={handleSubmit} style={styles.form}>
            <label style={styles.inputLabel}>
              Enter your name for the leaderboard:
            </label>
            <input
              ref={inputRef}
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              maxLength={20}
              placeholder="Your name"
              style={styles.input}
              disabled={isSubmitting}
            />
            <div style={styles.inputHint}>
              {playerName.length}/20 characters
            </div>
            
            <div style={styles.buttonRow}>
              <button
                type="button"
                onClick={onSkip}
                style={styles.skipButton}
                disabled={isSubmitting}
              >
                Skip
              </button>
              <button
                type="submit"
                style={{
                  ...styles.submitButton,
                  opacity: playerName.trim() ? 1 : 0.5,
                }}
                disabled={!playerName.trim() || isSubmitting}
              >
                {isSubmitting ? 'Saving...' : 'Submit Score'}
              </button>
            </div>
          </form>
        ) : (
          <div style={styles.notHighScore}>
            <p>Your score didn&apos;t make the top 10 this time.</p>
            <p>Keep practicing to get on the leaderboard!</p>
            <button onClick={onSkip} style={styles.continueButton}>
              Continue
            </button>
          </div>
        )}

        {/* Leaderboard Teaser */}
        <div style={styles.teaser}>
          <span>🏆 View the full leaderboard from the main menu</span>
        </div>
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
    background: 'rgba(0, 0, 0, 0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  container: {
    background: 'linear-gradient(135deg, #1f2937 0%, #111827 100%)',
    borderRadius: '20px',
    padding: '40px',
    width: '100%',
    maxWidth: '500px',
    textAlign: 'center',
    boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)',
    border: '1px solid #374151',
  },
  header: {
    marginBottom: '24px',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '32px',
    color: 'white',
  },
  scoreDisplay: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
  },
  scoreLabel: {
    fontSize: '14px',
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: '2px',
  },
  scoreValue: {
    fontSize: '56px',
    fontWeight: 'bold',
    color: '#fbbf24',
    fontFamily: 'monospace',
    textShadow: '0 0 20px rgba(251, 191, 36, 0.3)',
  },
  encouragement: {
    padding: '16px',
    background: 'rgba(59, 130, 246, 0.1)',
    borderRadius: '12px',
    marginBottom: '24px',
    fontSize: '16px',
    color: '#93c5fd',
    border: '1px solid rgba(59, 130, 246, 0.3)',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: '12px',
    marginBottom: '24px',
  },
  statBox: {
    padding: '12px',
    background: '#374151',
    borderRadius: '8px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  statLabel: {
    fontSize: '12px',
    color: '#9ca3af',
    textTransform: 'uppercase',
  },
  statValue: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: 'white',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  inputLabel: {
    fontSize: '14px',
    color: '#9ca3af',
  },
  input: {
    padding: '16px',
    fontSize: '20px',
    background: '#111827',
    border: '2px solid #374151',
    borderRadius: '12px',
    color: 'white',
    textAlign: 'center',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  inputHint: {
    fontSize: '12px',
    color: '#6b7280',
  },
  buttonRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '8px',
  },
  skipButton: {
    flex: 1,
    padding: '14px',
    background: 'transparent',
    border: '2px solid #6b7280',
    borderRadius: '10px',
    color: '#9ca3af',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  submitButton: {
    flex: 2,
    padding: '14px',
    background: 'linear-gradient(to right, #22c55e, #16a34a)',
    border: 'none',
    borderRadius: '10px',
    color: 'white',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  notHighScore: {
    padding: '24px',
    background: 'rgba(107, 114, 128, 0.1)',
    borderRadius: '12px',
    marginBottom: '16px',
  },
  continueButton: {
    padding: '14px 40px',
    background: '#3b82f6',
    border: 'none',
    borderRadius: '10px',
    color: 'white',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    marginTop: '16px',
  },
  teaser: {
    marginTop: '24px',
    padding: '12px',
    fontSize: '13px',
    color: '#6b7280',
    borderTop: '1px solid #374151',
  },
};

export default NameEntryModal;
