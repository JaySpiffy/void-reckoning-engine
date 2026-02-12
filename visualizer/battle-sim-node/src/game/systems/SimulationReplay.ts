/**
 * SIMULATION REPLAY SYSTEM
 * 
 * Records game state at intervals and allows playback
 * Useful for analyzing AI decisions and sharing interesting runs
 */

import type { Vector2 } from '../types';
import type { DNAType } from '../types';

export interface ReplayFrame {
  timestamp: number; // Game time in seconds
  wave: number;
  player: {
    position: Vector2;
    health: number;
    maxHealth: number;
    mana: number;
    level: number;
    dna: Record<DNAType, number>;
    dominantType: DNAType;
    purity: number;
  };
  enemies: Array<{
    id: string;
    type: string;
    position: Vector2;
    health: number;
  }>;
  buildings: Array<{
    id: string;
    type: string;
    position: Vector2;
    health: number;
  }>;
  resources: {
    wood: number;
    stone: number;
    gold: number;
    mana: number;
  };
  mutations: number;
  evolutionPaths: string[];
  aiDecisions: AIDecision[];
}

export interface AIDecision {
  timestamp: number;
  type: 'evolution' | 'mutation' | 'building' | 'target' | 'ability';
  decision: string;
  reason: string;
  position?: Vector2;
}

export interface SimulationReplay {
  id: string;
  version: string;
  startTime: string;
  config: {
    speed: number;
    useSmartAI: boolean;
    maxDuration: number;
  };
  frames: ReplayFrame[];
  finalResult: {
    wavesCompleted: number;
    score: number;
    success: boolean;
    causeOfDeath?: string;
  };
  statistics: {
    totalFrames: number;
    duration: number;
    avgFPS: number;
    keyEvents: AIDecision[];
  };
}

const REPLAY_STORAGE_KEY = 'simulation_replays_v1';
const MAX_REPLAYS = 20;
const FRAME_INTERVAL = 0.5; // Record every 0.5 seconds of game time

class SimulationReplaySystem {
  private currentReplay: SimulationReplay | null = null;
  private isRecording: boolean = false;
  private lastFrameTime: number = 0;
  private frameCount: number = 0;

  /**
   * Start recording a new replay
   */
  startRecording(config: { speed: number; useSmartAI: boolean; maxDuration: number }): string {
    const replayId = `replay_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.currentReplay = {
      id: replayId,
      version: '1.0',
      startTime: new Date().toISOString(),
      config,
      frames: [],
      finalResult: {
        wavesCompleted: 0,
        score: 0,
        success: false,
      },
      statistics: {
        totalFrames: 0,
        duration: 0,
        avgFPS: 0,
        keyEvents: [],
      },
    };
    
    this.isRecording = true;
    this.lastFrameTime = 0;
    this.frameCount = 0;
    
    console.log(`[Replay] Started recording ${replayId}`);
    return replayId;
  }

  /**
   * Record a frame if enough time has passed
   */
  recordFrame(gameTime: number, frameData: Omit<ReplayFrame, 'timestamp'>): void {
    if (!this.isRecording || !this.currentReplay) return;
    
    // Only record at intervals
    if (gameTime - this.lastFrameTime < FRAME_INTERVAL) return;
    
    const frame: ReplayFrame = {
      timestamp: gameTime,
      ...frameData,
    };
    
    this.currentReplay.frames.push(frame);
    this.lastFrameTime = gameTime;
    this.frameCount++;
    
    // Limit frames to prevent memory issues (max 10 minutes at 2fps = 1200 frames)
    if (this.currentReplay.frames.length > 1200) {
      this.currentReplay.frames.shift(); // Remove oldest frame
    }
  }

  /**
   * Record an AI decision
   */
  recordDecision(decision: Omit<AIDecision, 'timestamp'>, gameTime: number): void {
    if (!this.isRecording || !this.currentReplay) return;
    
    const fullDecision: AIDecision = {
      timestamp: gameTime,
      ...decision,
    };
    
    this.currentReplay.statistics.keyEvents.push(fullDecision);
    
    // Also add to current frame if exists
    const currentFrame = this.currentReplay.frames[this.currentReplay.frames.length - 1];
    if (currentFrame) {
      currentFrame.aiDecisions.push(fullDecision);
    }
  }

  /**
   * Stop recording and save
   */
  stopRecording(finalResult: SimulationReplay['finalResult']): SimulationReplay | null {
    if (!this.isRecording || !this.currentReplay) return null;
    
    this.currentReplay.finalResult = finalResult;
    this.currentReplay.statistics.totalFrames = this.frameCount;
    this.currentReplay.statistics.duration = this.lastFrameTime;
    this.currentReplay.statistics.avgFPS = this.frameCount / Math.max(this.lastFrameTime, 1);
    
    this.saveReplay(this.currentReplay);
    
    console.log(`[Replay] Stopped recording ${this.currentReplay.id}`, {
      frames: this.frameCount,
      duration: this.lastFrameTime.toFixed(1) + 's',
    });
    
    const replay = this.currentReplay;
    this.currentReplay = null;
    this.isRecording = false;
    
    return replay;
  }

  /**
   * Get replay by ID
   */
  getReplay(id: string): SimulationReplay | null {
    const replays = this.getSavedReplays();
    return replays.find(r => r.id === id) || null;
  }

  /**
   * Get all saved replays
   */
  getSavedReplays(): SimulationReplay[] {
    try {
      const saved = localStorage.getItem(REPLAY_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  }

  /**
   * Export replay to JSON string
   */
  exportReplay(id: string): string | null {
    const replay = this.getReplay(id);
    if (!replay) return null;
    return JSON.stringify(replay, null, 2);
  }

  /**
   * Import replay from JSON string
   */
  importReplay(json: string): SimulationReplay | null {
    try {
      const replay: SimulationReplay = JSON.parse(json);
      
      // Validate
      if (!replay.id || !replay.frames || !Array.isArray(replay.frames)) {
        throw new Error('Invalid replay format');
      }
      
      this.saveReplay(replay);
      return replay;
    } catch (error) {
      console.error('Failed to import replay:', error);
      return null;
    }
  }

  /**
   * Delete a replay
   */
  deleteReplay(id: string): void {
    const replays = this.getSavedReplays().filter(r => r.id !== id);
    localStorage.setItem(REPLAY_STORAGE_KEY, JSON.stringify(replays));
  }

  /**
   * Get replay statistics summary
   */
  getReplaySummary(id: string): {
    id: string;
    date: string;
    duration: number;
    waves: number;
    success: boolean;
    frameCount: number;
    keyEvents: number;
  } | null {
    const replay = this.getReplay(id);
    if (!replay) return null;
    
    return {
      id: replay.id,
      date: replay.startTime,
      duration: replay.statistics.duration,
      waves: replay.finalResult.wavesCompleted,
      success: replay.finalResult.success,
      frameCount: replay.statistics.totalFrames,
      keyEvents: replay.statistics.keyEvents.length,
    };
  }

  /**
   * Check if currently recording
   */
  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Get current recording progress
   */
  getRecordingProgress(): { time: number; frames: number } | null {
    if (!this.isRecording) return null;
    return {
      time: this.lastFrameTime,
      frames: this.frameCount,
    };
  }

  // Private helpers
  private saveReplay(replay: SimulationReplay): void {
    try {
      const replays = this.getSavedReplays();
      
      // Check if already exists
      const existingIndex = replays.findIndex(r => r.id === replay.id);
      if (existingIndex >= 0) {
        replays[existingIndex] = replay;
      } else {
        replays.unshift(replay);
      }
      
      // Keep only MAX_REPLAYS
      if (replays.length > MAX_REPLAYS) {
        replays.splice(MAX_REPLAYS);
      }
      
      localStorage.setItem(REPLAY_STORAGE_KEY, JSON.stringify(replays));
    } catch (error) {
      console.error('Failed to save replay:', error);
    }
  }
}

export const simulationReplay = new SimulationReplaySystem();
