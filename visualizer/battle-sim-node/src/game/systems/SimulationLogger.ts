/**
 * SIMULATION LOGGER - Structured logging for simulation sessions
 * 
 * Provides:
 * - Session-based logging with unique IDs
 * - Structured JSON logs for analysis
 * - File-based persistence
 * - Log rotation and cleanup
 */

import type { SimulationResult, SimulationConfig } from './SimulationManager';

export interface SimulationSession {
  id: string;
  startTime: string;
  endTime?: string;
  config: SimulationConfig;
  results: SimulationResult[];
  metrics: SessionMetrics;
}

export interface SessionMetrics {
  totalRuns: number;
  successfulRuns: number;
  averageWaves: number;
  averageScore: number;
  totalEnemiesKilled: number;
  totalEvolutions: number;
  totalMutations: number;
  totalBuildings: number;
  causesOfDeath: Record<string, number>;
  dnaTypesAcquired: Record<string, number>;
  evolutionPathsTaken: Record<string, number>;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  category: string;
  message: string;
  data?: unknown;
}

const STORAGE_KEY = 'simulation_sessions_v1';
const MAX_SESSIONS = 50; // Keep last 50 sessions

class SimulationLogger {
  private currentSession: SimulationSession | null = null;
  private logs: LogEntry[] = [];
  private isRecording: boolean = false;

  /**
   * Start a new simulation session
   */
  startSession(config: SimulationConfig): string {
    const sessionId = this.generateSessionId();
    
    this.currentSession = {
      id: sessionId,
      startTime: new Date().toISOString(),
      config,
      results: [],
      metrics: this.createEmptyMetrics(),
    };
    
    this.isRecording = true;
    this.log('info', 'Session', `Started simulation session ${sessionId}`, { config });
    
    return sessionId;
  }

  /**
   * End current session and save
   */
  endSession(): SimulationSession | null {
    if (!this.currentSession) return null;
    
    this.currentSession.endTime = new Date().toISOString();
    this.calculateFinalMetrics();
    
    this.log('info', 'Session', `Ended session ${this.currentSession.id}`, {
      duration: this.getSessionDuration(),
      totalRuns: this.currentSession.results.length,
    });
    
    // Save to storage
    this.saveSession(this.currentSession);
    
    const session = this.currentSession;
    this.currentSession = null;
    this.isRecording = false;
    this.logs = [];
    
    return session;
  }

  /**
   * Log a simulation result
   */
  logResult(result: SimulationResult): void {
    if (!this.currentSession || !this.isRecording) return;
    
    this.currentSession.results.push(result);
    this.updateMetrics(result);
    
    this.log('info', 'Simulation', `Completed simulation ${result.id}`, {
      waves: result.wavesCompleted,
      success: result.success,
      score: result.score,
    });
  }

  /**
   * Log a generic event
   */
  log(level: LogEntry['level'], category: string, message: string, data?: unknown): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
    };
    
    this.logs.push(entry);
    
    // Also log to console for debugging
    const consoleMethod = level === 'error' ? console.error : 
                          level === 'warn' ? console.warn : 
                          level === 'debug' ? console.debug : console.log;
    consoleMethod(`[${category}] ${message}`, data || '');
  }

  /**
   * Get current session stats
   */
  getCurrentStats(): Partial<SessionMetrics> | null {
    if (!this.currentSession) return null;
    return this.currentSession.metrics;
  }

  /**
   * Get session duration in seconds
   */
  getSessionDuration(): number {
    if (!this.currentSession) return 0;
    const start = new Date(this.currentSession.startTime).getTime();
    const end = this.currentSession.endTime 
      ? new Date(this.currentSession.endTime).getTime()
      : Date.now();
    return Math.floor((end - start) / 1000);
  }

  /**
   * Get all saved sessions
   */
  getSavedSessions(): SimulationSession[] {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  }

  /**
   * Export session to JSON file
   */
  exportSession(sessionId: string): string | null {
    const sessions = this.getSavedSessions();
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return null;
    
    return JSON.stringify(session, null, 2);
  }

  /**
   * Delete old sessions
   */
  cleanupOldSessions(maxAgeDays: number = 7): void {
    const sessions = this.getSavedSessions();
    const cutoff = Date.now() - (maxAgeDays * 24 * 60 * 60 * 1000);
    
    const filtered = sessions.filter(s => {
      const sessionTime = new Date(s.startTime).getTime();
      return sessionTime > cutoff;
    });
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    this.log('info', 'Cleanup', `Removed ${sessions.length - filtered.length} old sessions`);
  }

  // Private helpers
  private generateSessionId(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private createEmptyMetrics(): SessionMetrics {
    return {
      totalRuns: 0,
      successfulRuns: 0,
      averageWaves: 0,
      averageScore: 0,
      totalEnemiesKilled: 0,
      totalEvolutions: 0,
      totalMutations: 0,
      totalBuildings: 0,
      causesOfDeath: {},
      dnaTypesAcquired: {},
      evolutionPathsTaken: {},
    };
  }

  private updateMetrics(result: SimulationResult): void {
    if (!this.currentSession) return;
    
    const m = this.currentSession.metrics;
    m.totalRuns++;
    
    if (result.success) {
      m.successfulRuns++;
    }
    
    // Update averages
    m.averageWaves = this.calculateAverage(m.averageWaves, result.wavesCompleted, m.totalRuns);
    m.averageScore = this.calculateAverage(m.averageScore, result.score, m.totalRuns);
    
    m.totalEnemiesKilled += result.enemiesKilled;
    m.totalEvolutions += result.evolutionHistory.length;
    
    // Track mutations (if available in result)
    if ('mutationsPurchased' in result) {
      m.totalMutations += (result as unknown as { mutationsPurchased: number }).mutationsPurchased;
    }
    
    // Track buildings (if available in result)
    if ('buildingsConstructed' in result) {
      m.totalBuildings += (result as unknown as { buildingsConstructed: number }).buildingsConstructed;
    }
    
    // Track cause of death
    if (result.causeOfDeath) {
      m.causesOfDeath[result.causeOfDeath] = (m.causesOfDeath[result.causeOfDeath] || 0) + 1;
    }
    
    // Track DNA types
    for (const [type, amount] of Object.entries(result.dnaAcquired)) {
      m.dnaTypesAcquired[type] = (m.dnaTypesAcquired[type] || 0) + amount;
    }
    
    // Track evolution paths
    for (const evo of result.evolutionHistory) {
      m.evolutionPathsTaken[evo.path] = (m.evolutionPathsTaken[evo.path] || 0) + 1;
    }
  }

  private calculateAverage(current: number, newValue: number, count: number): number {
    return ((current * (count - 1)) + newValue) / count;
  }

  private calculateFinalMetrics(): void {
    // Any final calculations can go here
  }

  private saveSession(session: SimulationSession): void {
    try {
      const sessions = this.getSavedSessions();
      sessions.unshift(session); // Add to beginning
      
      // Keep only MAX_SESSIONS
      if (sessions.length > MAX_SESSIONS) {
        sessions.splice(MAX_SESSIONS);
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }
}

export const simulationLogger = new SimulationLogger();
