// ===== LEADERBOARD SERVICE =====
// Persistent leaderboard with localStorage

export interface LeaderboardEntry {
  id: string;
  playerName: string;
  score: number;
  gameMode: 'survival' | 'simulation';
  metadata: {
    // Legacy fields (kept for backward compatibility)
    teamName?: string;
    finalScore?: string;
    wavesSurvived?: number;
    timeAlive?: number;
    // Legacy field from football game
touchdowns?: number;
    date: string;
  };
}

export interface LeaderboardFilters {
  gameMode?: 'survival' | 'simulation';
  limit?: number;
}

const STORAGE_KEY = 'darwins_island_leaderboard_v1';
const MAX_ENTRIES = 100;

class LeaderboardService {
  private entries: LeaderboardEntry[] = [];
  private listeners: Set<(entries: LeaderboardEntry[]) => void> = new Set();

  constructor() {
    this.loadFromStorage();
  }

  // ===== CRUD OPERATIONS =====

  addEntry(entry: Omit<LeaderboardEntry, 'id' | 'metadata'> & { metadata?: Partial<LeaderboardEntry['metadata']> }): LeaderboardEntry {
    const newEntry: LeaderboardEntry = {
      ...entry,
      id: this.generateId(),
      metadata: {
        date: new Date().toISOString(),
        ...entry.metadata,
      },
    };

    this.entries.push(newEntry);
    this.sortEntries();
    this.trimEntries();
    this.saveToStorage();
    this.notifyListeners();

    return newEntry;
  }

  getEntries(filters?: LeaderboardFilters): LeaderboardEntry[] {
    let filtered = [...this.entries];

    if (filters?.gameMode) {
      filtered = filtered.filter(e => e.gameMode === filters.gameMode);
    }

    // Sort by score (descending)
    filtered.sort((a, b) => b.score - a.score);

    if (filters?.limit) {
      filtered = filtered.slice(0, filters.limit);
    }

    return filtered;
  }

  getTopEntry(gameMode?: 'survival' | 'simulation'): LeaderboardEntry | null {
    const entries = this.getEntries({ gameMode, limit: 1 });
    return entries[0] || null;
  }

  getPlayerRank(playerName: string, gameMode?: 'survival' | 'simulation'): number {
    const entries = this.getEntries({ gameMode });
    const index = entries.findIndex(e => e.playerName === playerName);
    return index >= 0 ? index + 1 : -1;
  }

  deleteEntry(id: string): boolean {
    const initialLength = this.entries.length;
    this.entries = this.entries.filter(e => e.id !== id);
    
    if (this.entries.length !== initialLength) {
      this.saveToStorage();
      this.notifyListeners();
      return true;
    }
    return false;
  }

  clearAll(): void {
    this.entries = [];
    this.saveToStorage();
    this.notifyListeners();
  }

  // ===== PERSISTENCE =====

  private loadFromStorage(): void {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (data) {
        this.entries = JSON.parse(data);
        this.sortEntries();
      }
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
      this.entries = [];
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.entries));
    } catch (error) {
      console.error('Failed to save leaderboard:', error);
    }
  }

  // ===== HELPERS =====

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private sortEntries(): void {
    this.entries.sort((a, b) => b.score - a.score);
  }

  private trimEntries(): void {
    if (this.entries.length > MAX_ENTRIES) {
      this.entries = this.entries.slice(0, MAX_ENTRIES);
    }
  }

  // ===== SUBSCRIPTIONS =====

  subscribe(callback: (entries: LeaderboardEntry[]) => void): () => void {
    this.listeners.add(callback);
    callback(this.entries);
    
    return () => {
      this.listeners.delete(callback);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(callback => callback(this.entries));
  }

  // ===== EXPORT/IMPORT =====

  exportToJSON(): string {
    return JSON.stringify(this.entries, null, 2);
  }

  importFromJSON(json: string): boolean {
    try {
      const data = JSON.parse(json);
      if (Array.isArray(data)) {
        this.entries = data;
        this.sortEntries();
        this.trimEntries();
        this.saveToStorage();
        this.notifyListeners();
        return true;
      }
    } catch (error) {
      console.error('Failed to import leaderboard:', error);
    }
    return false;
  }

  // ===== STATISTICS =====

  getStats(gameMode?: 'survival' | 'simulation'): {
    totalEntries: number;
    averageScore: number;
    highestScore: number;
    lowestScore: number;
    uniquePlayers: number;
  } {
    const entries = this.getEntries({ gameMode });
    
    if (entries.length === 0) {
      return {
        totalEntries: 0,
        averageScore: 0,
        highestScore: 0,
        lowestScore: 0,
        uniquePlayers: 0,
      };
    }

    const scores = entries.map(e => e.score);
    const uniquePlayers = new Set(entries.map(e => e.playerName)).size;

    return {
      totalEntries: entries.length,
      averageScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      highestScore: Math.max(...scores),
      lowestScore: Math.min(...scores),
      uniquePlayers,
    };
  }
}

// Singleton instance
export const leaderboard = new LeaderboardService();

// React hook for using leaderboard
export function useLeaderboard(filters?: LeaderboardFilters) {
  const [entries, setEntries] = React.useState<LeaderboardEntry[]>([]);
  
  React.useEffect(() => {
    // Initial load
    setEntries(leaderboard.getEntries(filters));
    
    // Subscribe to changes
    return leaderboard.subscribe(() => {
      setEntries(leaderboard.getEntries(filters));
    });
  }, [filters?.gameMode, filters?.limit]);

  return entries;
}

// Need to import React for the hook
import React from 'react';

export default leaderboard;
