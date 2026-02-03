import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';
import type { BattlePerformance, EconomicHealth } from '../types/telemetry';

interface BattlePerformanceChartProps {
  data: Record<string, BattlePerformance>;
}

export const BattlePerformanceChart: React.FC<BattlePerformanceChartProps> = ({ data }) => {
  const chartData = Object.entries(data).map(([faction, stats]) => ({
    name: faction.split('_')[0].substring(0, 10), // Short name
    cer: stats.avg_cer,
    attrition: stats.latest_attrition * 100,
  })).sort((a, b) => b.cer - a.cer).slice(0, 10); // Top 10

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
        <XAxis type="number" stroke="#6b7280" />
        <YAxis dataKey="name" type="category" width={80} tick={{fontSize: 10, fill: '#9ca3af'}} stroke="#4b5563" />
        <Tooltip
            contentStyle={{ backgroundColor: '#1a1d26', borderColor: '#374151', color: '#e0e6ed' }}
            itemStyle={{ color: '#e0e6ed' }}
        />
        <Legend wrapperStyle={{ paddingTop: '10px' }} />
        <Bar dataKey="cer" fill="#3b82f6" name="Efficiency (CER)" radius={[0, 4, 4, 0]} barSize={20} />
        <Bar dataKey="attrition" fill="#ef4444" name="Attrition %" radius={[0, 4, 4, 0]} barSize={20} />
      </BarChart>
    </ResponsiveContainer>
  );
};

interface EconomyChartProps {
    data: Record<string, EconomicHealth>;
}

export const EconomyChart: React.FC<EconomyChartProps> = ({ data }) => {
    const chartData = Object.entries(data).map(([faction, stats]) => ({
        name: faction.split('_')[0].substring(0, 10),
        income: stats.gross_income,
        upkeep: stats.total_upkeep,
        profit: stats.net_profit
    })).sort((a, b) => b.income - a.income).slice(0, 10);

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{top: 5, right: 30, left: 20, bottom: 5}}>
                <XAxis dataKey="name" tick={{fontSize: 10, fill: '#9ca3af'}} stroke="#4b5563" />
                <YAxis stroke="#4b5563" tick={{fill: '#9ca3af'}} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: '#1a1d26', borderColor: '#374151', color: '#e0e6ed' }} />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Bar dataKey="income" fill="#22c55e" name="Gross Income" radius={[4, 4, 0, 0]} />
                <Bar dataKey="upkeep" fill="#f59e0b" name="Total Upkeep" radius={[4, 4, 0, 0]} />
                <ReferenceLine y={0} stroke="#374151" />
            </BarChart>
        </ResponsiveContainer>
    );
};
