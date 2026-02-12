import { useState, useEffect } from 'react';
import { type LootDrop, LootRarity } from '../systems/LootSystem';
import { GameEvent } from '../types/events';
import { globalEvents } from '../utils';

interface LootNotification {
  id: string;
  drop: LootDrop;
  timestamp: number;
}

const RARITY_COLORS: Record<LootRarity, { bg: string; border: string; text: string; glow: string }> = {
  [LootRarity.COMMON]: {
    bg: 'bg-gray-800/90',
    border: 'border-gray-600',
    text: 'text-gray-300',
    glow: 'shadow-gray-500/20',
  },
  [LootRarity.UNCOMMON]: {
    bg: 'bg-green-900/90',
    border: 'border-green-600',
    text: 'text-green-300',
    glow: 'shadow-green-500/30',
  },
  [LootRarity.RARE]: {
    bg: 'bg-blue-900/90',
    border: 'border-blue-500',
    text: 'text-blue-300',
    glow: 'shadow-blue-500/40',
  },
  [LootRarity.EPIC]: {
    bg: 'bg-purple-900/90',
    border: 'border-purple-500',
    text: 'text-purple-300',
    glow: 'shadow-purple-500/50',
  },
  [LootRarity.LEGENDARY]: {
    bg: 'bg-gradient-to-r from-orange-900/90 to-red-900/90',
    border: 'border-orange-500',
    text: 'text-orange-300',
    glow: 'shadow-orange-500/60',
  },
};

const RARITY_ICONS: Record<LootRarity, string> = {
  [LootRarity.COMMON]: '⚪',
  [LootRarity.UNCOMMON]: '🟢',
  [LootRarity.RARE]: '🔵',
  [LootRarity.EPIC]: '🟣',
  [LootRarity.LEGENDARY]: '🟠',
};

export const LootNotifications = () => {
  const [notifications, setNotifications] = useState<LootNotification[]>([]);

  useEffect(() => {
    const handleLootAcquired = (data: { item?: { icon: string; name: string }; drop?: LootDrop }) => {
      // Handle full loot drops from enemy kills
      if (data.drop) {
        const notification: LootNotification = {
          id: Math.random().toString(36).substr(2, 9),
          drop: data.drop,
          timestamp: Date.now(),
        };
        setNotifications(prev => [notification, ...prev].slice(0, 5));
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
          setNotifications(prev => prev.filter(n => n.id !== notification.id));
        }, 4000);
      }
    };

    globalEvents.on(GameEvent.LOOT_ACQUIRED, handleLootAcquired);
    return () => globalEvents.off(GameEvent.LOOT_ACQUIRED, handleLootAcquired);
  }, []);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed right-4 top-24 z-40 flex flex-col gap-2 pointer-events-none">
      {notifications.map((notification, index) => {
        const { drop, id } = notification;
        const colors = RARITY_COLORS[drop.rarity];
        const icon = RARITY_ICONS[drop.rarity];
        
        return (
          <div
            key={id}
            className={`${colors.bg} ${colors.border} ${colors.glow} border rounded-lg p-3 shadow-lg backdrop-blur-sm animate-slide-in-right`}
            style={{
              animationDelay: `${index * 100}ms`,
              minWidth: '250px',
            }}
          >
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{icon}</span>
              <span className={`${colors.text} font-bold text-sm uppercase tracking-wider`}>
                {drop.rarity} Drop!
              </span>
            </div>
            
            {/* DNA Reward */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🧬</span>
              <div>
                <div className="text-white font-bold">
                  +{Math.floor(drop.dnaAmount)} {drop.dnaType} DNA
                </div>
                <div className="text-gray-400 text-xs">Absorbed from enemy</div>
              </div>
            </div>
            
            {/* Items */}
            {drop.items.length > 0 && (
              <div className="space-y-1 mt-2 pt-2 border-t border-white/10">
                {drop.items.map((item, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-lg">{item.icon}</span>
                    <span className="text-white text-sm">{item.name}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Mutation chance indicator */}
            {drop.mutationChance > 0 && (
              <div className="mt-2 text-xs text-yellow-400/80">
                {Math.floor(drop.mutationChance * 100)}% mutation chance
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
