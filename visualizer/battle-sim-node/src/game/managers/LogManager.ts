
export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}

export enum LogCategory {
    SYSTEM = 'SYSTEM',
    GAMEPLAY = 'GAMEPLAY',
    INPUT = 'INPUT',
    COMBAT = 'COMBAT',
    AI = 'AI',
    TEST = 'TEST',
    ABILITY = 'ABILITY',
    AUTOPLAY = 'AUTOPLAY',
    KEYBINDING = 'KEYBINDING',
    WAVE = 'WAVE',
    NPC = 'NPC'
}

export interface LogEntry {
    timestamp: number;
    level: LogLevel;
    category: LogCategory;
    message: string;
    data?: unknown;
}

class LogManager {
    private logs: LogEntry[] = [];
    private minLevel: LogLevel = LogLevel.DEBUG; // Default to DEBUG for now, can change based on env
    private maxLogs: number = 1000;

    constructor() {
        // Auto-detect production environment to silence debug logs
        if (import.meta.env && import.meta.env.PROD) {
            this.minLevel = LogLevel.INFO;
        }
    }

    public setLevel(level: LogLevel): void {
        this.minLevel = level;
    }

    private log(level: LogLevel, category: LogCategory, message: string, data?: unknown): void {
        if (level < this.minLevel) return;

        const entry: LogEntry = {
            timestamp: Date.now(),
            level,
            category,
            message,
            data
        };

        this.logs.push(entry);
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        // Format for console
        const prefix = `[${category}]`;
        const style = this.getStyle(level);

        /* eslint-disable no-console */
        if (data) {
            console.log(`%c${prefix} ${message}`, style, data);
        } else {
            console.log(`%c${prefix} ${message}`, style);
        }
        /* eslint-enable no-console */
    }

    private getStyle(level: LogLevel): string {
        switch (level) {
            case LogLevel.DEBUG: return 'color: #9E9E9E';
            case LogLevel.INFO: return 'color: #2196F3';
            case LogLevel.WARN: return 'color: #FFC107; font-weight: bold';
            case LogLevel.ERROR: return 'color: #F44336; font-weight: bold';
            default: return '';
        }
    }

    public debug(category: LogCategory, message: string, data?: unknown) {
        this.log(LogLevel.DEBUG, category, message, data);
    }

    public info(category: LogCategory, message: string, data?: unknown) {
        this.log(LogLevel.INFO, category, message, data);
    }

    public warn(category: LogCategory, message: string, data?: unknown) {
        this.log(LogLevel.WARN, category, message, data);
    }

    public error(category: LogCategory, message: string, data?: unknown) {
        this.log(LogLevel.ERROR, category, message, data);
    }

    public getLogs(): LogEntry[] {
        return [...this.logs];
    }

    public clear(): void {
        this.logs = [];
    }
}

export const logger = new LogManager();

// Expose for testing
if (typeof window !== 'undefined') {
    (window as { logger?: LogManager } & Window).logger = logger;
}
