import React from 'react';
import { Layout } from './Layout';
import { StatCard } from './StatCard';
import { FactionTable } from './FactionTable';
import { BattlePerformanceChart, EconomyChart } from './Charts';
import { useWebSocket } from '../hooks/useWebSocket';
import type { LiveMetrics } from '../types/telemetry';
import { Crosshair, Hammer, Coins, Globe } from 'lucide-react';

export const Dashboard: React.FC = () => {
    // Connect to /ws relative path (proxy handles it)
    const { data, isConnected } = useWebSocket<LiveMetrics>('/ws');

    // Default empty data to prevent crashes
    const safeData: Partial<LiveMetrics> = data || {};

    // Aggregates
    const totalBattles = safeData.battles?.total || 0;
    const battleRate = safeData.battles?.rate || 0;

    const totalConstruction = safeData.construction?.total || 0;
    const constRate = Object.values(safeData.construction?.rate || {}).reduce((a, b) => a + b, 0);

    const totalRevenue = safeData.economy?.total_revenue || 0;
    const totalSpawned = safeData.units?.total_spawned || 0;

    return (
        <Layout connected={isConnected} turn={safeData.turn || 0}>
            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <StatCard
                    label="Total Battles"
                    value={totalBattles}
                    subValue={`${battleRate.toFixed(2)} / sec`}
                    icon={Crosshair}
                    color="text-red-500"
                />
                <StatCard
                    label="Units Deployed"
                    value={totalSpawned}
                    subValue="Total Forces"
                    icon={Globe}
                    color="text-blue-500"
                />
                <StatCard
                    label="Construction"
                    value={totalConstruction}
                    subValue={`${constRate.toFixed(1)} / sec`}
                    icon={Hammer}
                    color="text-yellow-500"
                />
                <StatCard
                    label="Global Revenue"
                    value={(totalRevenue / 1000).toFixed(1) + 'k'}
                    subValue="Total Credits"
                    icon={Coins}
                    color="text-green-500"
                />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Main Faction Table (Spans 2 cols) */}
                <div className="xl:col-span-2 space-y-6">
                    <FactionTable
                        data={safeData.faction_status || {}}
                    />

                     {/* Economy Chart Section */}
                    <div className="bg-bg-card border border-gray-800 rounded-lg p-4 h-[350px]">
                        <h3 className="font-semibold text-sm uppercase tracking-wider text-text-secondary mb-4">Economic Performance (Income vs Upkeep)</h3>
                        <EconomyChart data={safeData.economic_health || {}} />
                    </div>
                </div>

                {/* Sidebar (Charts) */}
                <div className="space-y-6">
                    {/* Battle Performance */}
                    <div className="bg-bg-card border border-gray-800 rounded-lg p-4 h-[400px]">
                         <h3 className="font-semibold text-sm uppercase tracking-wider text-text-secondary mb-4">Combat Efficiency</h3>
                         <BattlePerformanceChart data={safeData.battle_performance || {}} />
                    </div>

                    {/* Planet Status (Simple List for now) */}
                    <div className="bg-bg-card border border-gray-800 rounded-lg p-4 h-[300px] overflow-hidden flex flex-col">
                        <h3 className="font-semibold text-sm uppercase tracking-wider text-text-secondary mb-4">Recent Planet Updates</h3>
                         <div className="overflow-y-auto flex-1 space-y-2 pr-2 custom-scrollbar">
                            {(safeData.planet_status || []).slice(0, 20).map((p, i) => (
                                <div key={i} className="flex justify-between items-center text-sm p-2 bg-gray-900/50 rounded border border-gray-800 hover:bg-gray-800/50 transition-colors">
                                    <span className="text-gray-300 font-mono truncate max-w-[120px]" title={p.name}>{p.name}</span>
                                    <span className="text-[10px] text-accent bg-blue-900/20 px-2 py-0.5 rounded border border-blue-900/50 truncate max-w-[100px]" title={p.owner}>
                                        {p.owner}
                                    </span>
                                </div>
                            ))}
                            {(!safeData.planet_status || safeData.planet_status.length === 0) && (
                                <div className="text-gray-600 italic text-center text-sm mt-10">Waiting for telemetry...</div>
                            )}
                         </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};
