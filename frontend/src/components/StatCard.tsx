import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon: LucideIcon;
  color?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subValue, icon: Icon, color = 'text-accent' }) => {
  return (
    <div className="bg-bg-card border border-gray-800 rounded-lg p-5 flex items-start justify-between hover:border-gray-700 transition-colors shadow-sm">
      <div>
        <h3 className="text-xs text-text-secondary uppercase tracking-widest font-semibold mb-1">{label}</h3>
        <div className="text-2xl font-bold text-white">{value}</div>
        {subValue && <div className="text-xs text-gray-500 mt-1">{subValue}</div>}
      </div>
      <div className={`p-2 rounded bg-gray-900/50 ${color}`}>
        <Icon size={24} />
      </div>
    </div>
  );
};
