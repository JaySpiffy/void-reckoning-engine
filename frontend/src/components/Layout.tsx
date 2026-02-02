import React from 'react';
import { Terminal, Activity } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  connected: boolean;
  turn: number;
}

export const Layout: React.FC<LayoutProps> = ({ children, connected, turn }) => {
  return (
    <div className="min-h-screen bg-bg-dark text-text-primary font-mono">
      {/* Header */}
      <header className="border-b border-gray-800 bg-bg-card px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-md">
        <div className="flex items-center gap-3">
          <Terminal className="text-accent" />
          <h1 className="text-xl font-bold tracking-wider">VOID RECKONING <span className="text-xs text-text-secondary font-normal">TELEMETRY LINK</span></h1>
        </div>

        <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-gray-500" />
                <span className="text-gray-400">TURN</span>
                <span className="text-xl font-bold text-white">{turn}</span>
            </div>

            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-success animate-pulse' : 'bg-error'}`} />
                <span className={connected ? 'text-success' : 'text-error'}>
                    {connected ? 'LIVE FEED' : 'OFFLINE'}
                </span>
            </div>
        </div>
      </header>

      <main className="p-6 max-w-[1600px] mx-auto">
        {children}
      </main>
    </div>
  );
};
