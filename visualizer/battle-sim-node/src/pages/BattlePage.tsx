import { useState, useMemo, useCallback } from 'react';
import { BattleGameManager } from '../game/managers/BattleGameManager';
import { BattleCanvas } from '../components/BattleCanvas';
import { Button } from '@/components/ui/button';
import { Team, TEAM_CONFIG } from '../game/types/battle';
import { ZoomIn, ZoomOut, Play, Pause, RotateCcw, Target, Activity, Settings2 } from 'lucide-react';
import { SIMULATION_CONFIG, BATTLE_PRESETS, applyPreset } from '../game/data/SimulationConfig';
import { VOID_UNIT_CLASSES } from '../game/data/VoidEngineData';

export function BattlePage() {
    const [game] = useState(() => new BattleGameManager());
    const [, setTick] = useState(0);
    const [camera, setCamera] = useState({ x: -50, y: -100, zoom: 1 });
    const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'status' | 'config'>('status');
    
    // Config state for sliders - use sensible defaults
    const [config, setConfig] = useState({
        teamSize: SIMULATION_CONFIG.teamSize,
        healthScale: 1.0,
        damageScale: 1.0,
        speedScale: 1.5,
    });

    useMemo(() => {
        const interval = setInterval(() => setTick(t => t + 1), 100);
        return () => clearInterval(interval);
    }, []);

    const stats = game.getStats();
    const blueStats = game.battle.getTeamStats(Team.BLUE);
    const redStats = game.battle.getTeamStats(Team.RED);
    const formations = game.battle.getFormationInfo();

    const handleStart = useCallback(() => { game.start(); setTick(t => t + 1); }, [game]);
    const handlePause = useCallback(() => { game.togglePause(); setTick(t => t + 1); }, [game]);
    
    const handleReset = useCallback(() => {
        game.reset();
        setCamera({ x: -50, y: -100, zoom: 1 });
        setSelectedUnit(null);
        setTick(t => t + 1);
    }, [game]);
    
    const handleApplyConfig = useCallback(() => {
        SIMULATION_CONFIG.teamSize = config.teamSize;
        SIMULATION_CONFIG.healthScale = config.healthScale;
        SIMULATION_CONFIG.damageScale = config.damageScale;
        SIMULATION_CONFIG.speedScale = config.speedScale;
        game.reset();
        setTick(t => t + 1);
    }, [config, game]);

    const handleSpeed = useCallback((speed: number) => { game.setTimeScale(speed); setTick(t => t + 1); }, [game]);
    const handleZoomIn = useCallback(() => setCamera(c => ({ ...c, zoom: Math.min(c.zoom * 1.2, 3) })), []);
    const handleZoomOut = useCallback(() => setCamera(c => ({ ...c, zoom: Math.max(c.zoom / 1.2, 0.3) })), []);
    const handleCameraMove = useCallback((dx: number, dy: number) => setCamera(c => ({ ...c, x: c.x + dx, y: c.y + dy })), []);

    const applyPresetConfig = (preset: keyof typeof BATTLE_PRESETS) => {
        applyPreset(preset);
        setConfig({
            teamSize: SIMULATION_CONFIG.teamSize,
            healthScale: SIMULATION_CONFIG.healthScale,
            damageScale: SIMULATION_CONFIG.damageScale,
            speedScale: SIMULATION_CONFIG.speedScale,
        });
        game.reset();
        setTick(t => t + 1);
    };

    const updateConfig = (key: keyof typeof config, value: number) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    const selectedUnitData = selectedUnit ? game.battle.getUnit(selectedUnit) : null;

    return (
        <div className="min-h-screen bg-slate-950 flex overflow-hidden">
            {/* Left Panel */}
            <div className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col overflow-hidden">
                {/* Header */}
                <div className="p-4 border-b border-slate-800">
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <Target className="text-violet-500" size={24} />
                        Void Reckoning
                    </h1>
                    <p className="text-slate-400 text-xs mt-1">Battle Simulator v0.2</p>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-800">
                    <button
                        onClick={() => setActiveTab('status')}
                        className={`flex-1 py-2 text-sm font-medium ${activeTab === 'status' ? 'text-violet-400 border-b-2 border-violet-400' : 'text-slate-400 hover:text-white'}`}
                    >
                        <Activity size={14} className="inline mr-1" /> Status
                    </button>
                    <button
                        onClick={() => setActiveTab('config')}
                        className={`flex-1 py-2 text-sm font-medium ${activeTab === 'config' ? 'text-violet-400 border-b-2 border-violet-400' : 'text-slate-400 hover:text-white'}`}
                    >
                        <Settings2 size={14} className="inline mr-1" /> Config
                    </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-y-auto">
                    {activeTab === 'status' ? (
                        <StatusTab 
                            game={game} 
                            stats={stats} 
                            blueStats={blueStats} 
                            redStats={redStats} 
                            formations={formations}
                            selectedUnitData={selectedUnitData}
                        />
                    ) : (
                        <ConfigTab 
                            config={config}
                            onChange={updateConfig}
                            onApply={handleApplyConfig}
                            onPreset={applyPresetConfig}
                        />
                    )}
                </div>
            </div>

            {/* Main Battle Area */}
            <div className="flex-1 flex flex-col">
                {/* Controls Bar */}
                <div className="bg-slate-900/80 border-b border-slate-800 px-4 py-2 flex gap-2 items-center">
                    <Button onClick={handleStart} disabled={game.battle.phase !== 'SETUP'}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 gap-1" size="sm">
                        <Play size={14} /> Start
                    </Button>
                    <Button onClick={handlePause} disabled={game.battle.phase !== 'BATTLE' || !!game.battle.winner}
                        className="bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50 gap-1" size="sm">
                        {game.isPaused ? <Play size={14} /> : <Pause size={14} />}
                    </Button>
                    <Button onClick={handleReset} variant="outline" className="border-slate-600 text-slate-300 gap-1" size="sm">
                        <RotateCcw size={14} /> Reset
                    </Button>

                    <div className="w-px h-5 bg-slate-700 mx-2" />

                    <span className="text-slate-500 text-xs">SPEED</span>
                    {[0.5, 1, 2, 5].map(speed => (
                        <Button key={speed} onClick={() => handleSpeed(speed)}
                            variant={game.timeScale === speed ? 'default' : 'outline'}
                            size="sm"
                            className={game.timeScale === speed ? 'bg-violet-600 text-white' : 'border-slate-600 text-slate-400'}>
                            {speed}x
                        </Button>
                    ))}

                    <div className="w-px h-5 bg-slate-700 mx-2" />

                    <span className="text-slate-500 text-xs">ZOOM</span>
                    <Button onClick={handleZoomIn} variant="outline" size="sm" className="border-slate-600 text-slate-400">
                        <ZoomIn size={14} />
                    </Button>
                    <Button onClick={handleZoomOut} variant="outline" size="sm" className="border-slate-600 text-slate-400">
                        <ZoomOut size={14} />
                    </Button>
                    <span className="text-slate-500 text-xs ml-1">{camera.zoom.toFixed(1)}x</span>

                    <div className="ml-auto text-xs text-slate-500">
                        {config.teamSize}v{config.teamSize} • Click unit → inspect
                    </div>
                </div>

                {/* Battle Canvas */}
                <div className="flex-1 relative overflow-hidden">
                    <BattleCanvas 
                        game={game} 
                        camera={camera} 
                        onCameraMove={handleCameraMove}
                        onUnitSelect={setSelectedUnit}
                        selectedUnit={selectedUnit}
                    />

                    {game.winner && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="text-6xl font-black px-10 py-5 rounded-2xl animate-pulse"
                                style={{
                                    color: TEAM_CONFIG[game.winner].color,
                                    textShadow: `0 0 60px ${TEAM_CONFIG[game.winner].color}`,
                                    background: 'rgba(0,0,0,0.8)',
                                    border: `4px solid ${TEAM_CONFIG[game.winner].color}`
                                }}>
                                {game.winner === Team.BLUE ? 'BLUE VICTORY' : 'RED VICTORY'}
                            </div>
                        </div>
                    )}

                    {game.isPaused && !game.winner && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="text-4xl font-bold text-amber-400 bg-black/60 px-6 py-3 rounded-xl border border-amber-400/30">
                                PAUSED
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom Stats */}
                <div className="bg-slate-900 border-t border-slate-800 px-4 py-2 flex justify-around text-sm">
                    <div className="text-center">
                        <div className="text-2xl font-bold" style={{ color: TEAM_CONFIG[Team.BLUE].color }}>{stats.blueAlive}</div>
                        <div className="text-slate-500 text-xs">Blue Alive</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{stats.blueKills + stats.redKills}</div>
                        <div className="text-slate-500 text-xs">Total Kills</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-mono font-bold text-white">{formatTime(stats.battleTime)}</div>
                        <div className="text-slate-500 text-xs">Battle Time</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{stats.redKills}</div>
                        <div className="text-slate-500 text-xs">Red Kills</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold" style={{ color: TEAM_CONFIG[Team.RED].color }}>{stats.redAlive}</div>
                        <div className="text-slate-500 text-xs">Red Alive</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Status Tab Component
function StatusTab({ game, stats, blueStats, redStats, formations, selectedUnitData }: any) {
    return (
        <div className="p-4 space-y-4">
            {/* Battle Status */}
            <div className="p-3 rounded-lg bg-slate-800/50">
                <h2 className="text-sm font-bold text-slate-300 mb-2 flex items-center gap-2">
                    <Activity size={16} /> Battle Status
                </h2>
                <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                        <span className="text-slate-500">Phase</span>
                        <span className={game.battle.phase === 'BATTLE' ? 'text-green-400' : game.battle.phase === 'FINISHED' ? 'text-yellow-400' : 'text-slate-300'}>
                            {game.battle.phase}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">Time</span>
                        <span className="text-white font-mono">{formatTime(stats.battleTime)}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">Speed</span>
                        <span className="text-violet-400">{game.timeScale.toFixed(1)}x</span>
                    </div>
                    {game.winner && (
                        <div className="mt-2 p-2 rounded text-center font-bold"
                            style={{ backgroundColor: `${TEAM_CONFIG[game.winner as Team].color}20`, color: TEAM_CONFIG[game.winner as Team].color }}>
                            {game.winner} WINS!
                        </div>
                    )}
                </div>
            </div>

            {/* Team Stats */}
            <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}>
                <div className="flex justify-between mb-1">
                    <span className="font-bold text-blue-400">Blue Force</span>
                    <span className="text-white font-mono">{blueStats.alive}/{blueStats.total}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-blue-500 transition-all" style={{ width: `${(blueStats.alive/blueStats.total)*100}%` }} />
                </div>
                <div className="text-xs text-slate-400 grid grid-cols-2 gap-1">
                    <span>Kills: {blueStats.killed}</span>
                    <span>Avg HP: {(blueStats.avgHealth*100).toFixed(0)}%</span>
                    {blueStats.interceptors > 0 && (
                        <span className="col-span-2 text-cyan-400">🛸 Drones: {blueStats.interceptors}</span>
                    )}
                </div>
            </div>

            <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                <div className="flex justify-between mb-1">
                    <span className="font-bold text-red-400">Red Force</span>
                    <span className="text-white font-mono">{redStats.alive}/{redStats.total}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2">
                    <div className="h-full bg-red-500 transition-all" style={{ width: `${(redStats.alive/redStats.total)*100}%` }} />
                </div>
                <div className="text-xs text-slate-400 grid grid-cols-2 gap-1">
                    <span>Kills: {redStats.killed}</span>
                    <span>Avg HP: {(redStats.avgHealth*100).toFixed(0)}%</span>
                    {redStats.interceptors > 0 && (
                        <span className="col-span-2 text-cyan-400">🛸 Drones: {redStats.interceptors}</span>
                    )}
                </div>
            </div>

            {/* Formations */}
            <div className="p-3 rounded-lg bg-slate-800/50">
                <h2 className="text-sm font-bold text-slate-300 mb-2">Formations</h2>
                <div className="text-xs text-slate-400 space-y-1">
                    <div>🔵 {formations.blue}</div>
                    <div>🔴 {formations.red}</div>
                </div>
            </div>

            {/* Selected Unit */}
            {selectedUnitData && (
                <div className="p-3 rounded-lg bg-slate-800/50 border border-violet-500/30">
                    <h2 className="text-sm font-bold text-violet-400 mb-2">Selected Unit</h2>
                    <div className="text-xs space-y-1 text-slate-300">
                        <div className="flex justify-between"><span className="text-slate-500">Name</span><span>{selectedUnitData.displayName}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Status</span><span className={selectedUnitData.isActive ? 'text-green-400' : 'text-red-400'}>{selectedUnitData.getStatusText()}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">HP</span><span>{Math.round(selectedUnitData.health)}/{Math.round(selectedUnitData.maxHealth)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Morale</span><span>{Math.round(selectedUnitData.morale)}/{Math.round(selectedUnitData.maxMorale)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Kills</span><span className="text-yellow-400">{selectedUnitData.kills}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Position</span><span className="font-mono">{selectedUnitData.getCoordinates()}</span></div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Config Tab Component with Sliders
function ConfigTab({ config, onChange, onApply, onPreset }: any) {
    return (
        <div className="p-4 space-y-4">
            {/* Presets */}
            <div className="p-3 rounded-lg bg-slate-800/50">
                <h2 className="text-sm font-bold text-slate-300 mb-3">Quick Presets</h2>
                <div className="grid grid-cols-2 gap-2">
                    {Object.keys(BATTLE_PRESETS).map(preset => (
                        <Button
                            key={preset}
                            onClick={() => onPreset(preset)}
                            variant="outline"
                            size="sm"
                            className="border-slate-600 text-slate-300 hover:bg-slate-700 text-xs"
                        >
                            {preset.charAt(0).toUpperCase() + preset.slice(1)}
                        </Button>
                    ))}
                </div>
            </div>

            {/* Sliders */}
            <div className="p-3 rounded-lg bg-slate-800/50 space-y-4">
                <h2 className="text-sm font-bold text-slate-300 mb-2">Simulation Parameters</h2>
                
                {/* Team Size */}
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Team Size</span>
                        <span className="text-violet-400 font-mono">{config.teamSize}</span>
                    </div>
                    <input
                        type="range"
                        min="10"
                        max="100"
                        step="5"
                        value={config.teamSize}
                        onChange={(e) => onChange('teamSize', parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                        <span>10</span>
                        <span>100</span>
                    </div>
                </div>

                {/* Health Scale */}
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Health Scale</span>
                        <span className="text-violet-400 font-mono">{config.healthScale.toFixed(1)}x</span>
                    </div>
                    <input
                        type="range"
                        min="0.1"
                        max="3.0"
                        step="0.1"
                        value={config.healthScale}
                        onChange={(e) => onChange('healthScale', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                        <span>0.1x (Fast)</span>
                        <span>3.0x (Tanky)</span>
                    </div>
                </div>

                {/* Damage Scale */}
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Damage Scale</span>
                        <span className="text-violet-400 font-mono">{config.damageScale.toFixed(1)}x</span>
                    </div>
                    <input
                        type="range"
                        min="0.1"
                        max="3.0"
                        step="0.1"
                        value={config.damageScale}
                        onChange={(e) => onChange('damageScale', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                        <span>0.01</span>
                        <span>0.5</span>
                    </div>
                </div>

                {/* Speed Scale */}
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Speed Scale</span>
                        <span className="text-violet-400 font-mono">{config.speedScale.toFixed(1)}x</span>
                    </div>
                    <input
                        type="range"
                        min="0.5"
                        max="3.0"
                        step="0.1"
                        value={config.speedScale}
                        onChange={(e) => onChange('speedScale', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                        <span>0.5x (Slow)</span>
                        <span>3.0x (Fast)</span>
                    </div>
                </div>
            </div>

            {/* Apply Button */}
            <Button 
                onClick={onApply}
                className="w-full bg-violet-600 hover:bg-violet-700 text-white"
                size="sm"
            >
                Apply & Reset Battle
            </Button>

            {/* Current Config Summary */}
            <div className="p-3 rounded-lg bg-slate-800/30 text-xs text-slate-400">
                <div className="font-bold text-slate-300 mb-1">Current Settings:</div>
                <div>{config.teamSize}v{config.teamSize} units</div>
                <div>Health: {config.healthScale}x | Damage: {config.damageScale}x</div>
                <div>Speed: {config.speedScale}x</div>
            </div>

            {/* Unit Types */}
            <div className="p-3 rounded-lg bg-slate-800/50">
                <h2 className="text-sm font-bold text-slate-300 mb-2">Available Units</h2>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                    {VOID_UNIT_CLASSES.filter(u => SIMULATION_CONFIG.availableUnitClasses.includes(u.id)).map(unit => (
                        <div key={unit.id} className="flex justify-between text-xs p-1.5 rounded bg-slate-800/50">
                            <span className="text-slate-300">{unit.name}</span>
                            <span className="text-slate-500">T{unit.tech_tier}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms}`;
}
