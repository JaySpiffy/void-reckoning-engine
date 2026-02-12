import { useState, useEffect, useCallback } from 'react';
import { ABILITY_CONFIGS, ElementType, ELEMENT_CONFIGS, GameEvent } from '../types';
import type { AbilityType } from '../types';
import type { AbilitySystem } from '../systems/AbilitySystem';
import { keybindingSystem, BindableAction } from '../systems/KeybindingSystem';
import { globalEvents } from '../utils';
import { lootSystem } from '../systems/LootSystem';
import type { LootItem } from '../systems/LootSystem';
import type { GameManager } from '../managers/GameManager';

interface ActionBarProps {
  abilitySystem: AbilitySystem;
  currentMana: number;
  maxMana: number;
  currentElement: ElementType;
  gameManager?: GameManager | null;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  ability: typeof ABILITY_CONFIGS[AbilityType] | null;
  item: LootItem | null; // Add item to tooltip state
}

// Slot configuration with action mapping
const SLOT_ACTIONS: BindableAction[] = [
  BindableAction.ABILITY_SLOT_1,
  BindableAction.ABILITY_SLOT_2,
  BindableAction.ABILITY_SLOT_3,
  BindableAction.ABILITY_SLOT_4,
  BindableAction.ABILITY_SLOT_5,
];

const ITEM_ACTIONS: BindableAction[] = [
  BindableAction.USE_ITEM_1,
  BindableAction.USE_ITEM_2,
  BindableAction.USE_ITEM_3,
];

export const ActionBar = ({
  abilitySystem,
  currentMana,
  maxMana,
  currentElement,
  gameManager
}: ActionBarProps) => {
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    ability: null,
    item: null,
  });
  const [, forceUpdate] = useState({});

  // Track pressed state for visual feedback
  const [pressedSlots, setPressedSlots] = useState<Set<number>>(new Set());
  const [pressedItems, setPressedItems] = useState<Set<number>>(new Set());

  // Force update every frame for cooldown progress
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate({});
    }, 50);
    return () => clearInterval(interval);
  }, [abilitySystem]);

  const triggerAbility = useCallback((slotIndex: number) => {
    if (!gameManager) {
      abilitySystem.useAbilitySlot(slotIndex);
      return;
    }

    // Get target position from game manager
    const worldPos = gameManager.screenToWorld(gameManager.getLastMousePosition());
    abilitySystem.useAbilitySlot(slotIndex, worldPos);
  }, [abilitySystem, gameManager]);

  const triggerItem = useCallback((itemIndex: number) => {
    const inventory = lootSystem.getInventory();
    if (inventory[itemIndex]) {
      lootSystem.useItem(inventory[itemIndex].id);
    }
  }, []);

  // Listen for key press events
  useEffect(() => {
    const handleKeyPress = (data: { action: BindableAction; pressed: boolean }) => {
      const slotIndex = SLOT_ACTIONS.indexOf(data.action);
      if (slotIndex !== -1) {
        setPressedSlots(prev => {
          const newSet = new Set(prev);
          if (data.pressed) {
            newSet.add(slotIndex);
          } else {
            newSet.delete(slotIndex);
          }
          return newSet;
        });

        // Trigger ability on press
        if (data.pressed) {
          triggerAbility(slotIndex + 1);
        }
      }

      const itemIndex = ITEM_ACTIONS.indexOf(data.action);
      if (itemIndex !== -1) {
        setPressedItems(prev => {
          const newSet = new Set(prev);
          if (data.pressed) {
            newSet.add(itemIndex);
          } else {
            newSet.delete(itemIndex);
          }
          return newSet;
        });

        if (data.pressed) {
          triggerItem(itemIndex);
        }
      }
    };

    globalEvents.on(GameEvent.KEYBINDING_PRESSED, handleKeyPress);
    return () => {
      globalEvents.off(GameEvent.KEYBINDING_PRESSED, handleKeyPress);
    };
  }, [abilitySystem, gameManager, triggerAbility, triggerItem]);

  const slots = abilitySystem.getSlots();
  const inventory = lootSystem.getInventory();

  const showTooltip = (abilityType: AbilityType, e: React.MouseEvent) => {
    const ability = ABILITY_CONFIGS[abilityType];
    setTooltip({
      visible: true,
      x: e.clientX,
      y: e.clientY - 100,
      ability,
      item: null,
    });
  };

  const showItemTooltip = (item: LootItem, e: React.MouseEvent) => {
    setTooltip({
      visible: true,
      x: e.clientX,
      y: e.clientY - 100,
      ability: null,
      item,
    });
  };

  const hideTooltip = () => {
    setTooltip(prev => ({ ...prev, visible: false }));
  };

  const getSlotColor = (slotIndex: number): string => {
    const abilityType = slots[slotIndex];
    const ability = ABILITY_CONFIGS[abilityType];

    if (ability.element === ElementType.NONE) {
      return currentElement === ElementType.NONE ? '#3b82f6' : ELEMENT_CONFIGS[currentElement].color;
    }

    return ELEMENT_CONFIGS[ability.element].color;
  };

  const getKeyDisplay = (slotIndex: number): string => {
    return keybindingSystem.getKeyDisplay(SLOT_ACTIONS[slotIndex]);
  };

  const getItemKeyDisplay = (itemIndex: number): string => {
    return keybindingSystem.getKeyDisplay(ITEM_ACTIONS[itemIndex]);
  };

  const renderTooltip = () => {
    if (!tooltip.visible) return null;

    if (tooltip.item) {
      const item = tooltip.item;
      return (
        <div
          className="fixed z-50 bg-black/95 border border-gray-600 rounded-lg p-3 pointer-events-none shadow-xl"
          style={{ left: tooltip.x, top: tooltip.y, minWidth: 200 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{item.icon}</span>
            <div>
              <div className="text-white font-bold">{item.name}</div>
              <div className="text-xs text-gray-400 capitalize">{item.type}</div>
            </div>
          </div>
          <div className="text-gray-300 text-sm">{item.description}</div>
        </div>
      );
    }

    if (tooltip.ability) {
      const ability = tooltip.ability;
      const isReady = abilitySystem.isAbilityReady(ability.id);
      const canAfford = currentMana >= ability.manaCost;
      const cooldownPercent = abilitySystem.getCooldownPercent(ability.id);

      return (
        <div
          className="fixed z-50 bg-black/95 border border-gray-600 rounded-lg p-3 pointer-events-none shadow-xl"
          style={{ left: tooltip.x, top: tooltip.y, minWidth: 220 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{ability.icon}</span>
            <div>
              <div className="text-white font-bold">{ability.name}</div>
              <div className="text-xs text-gray-400">
                {ability.element !== ElementType.NONE ? ability.element : 'Basic'} Ability
              </div>
            </div>
          </div>

          <div className="text-gray-300 text-sm mb-2">{ability.description}</div>

          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Damage:</span>
              <span className="text-yellow-400">{ability.damage}</span>
            </div>

            {ability.dotDamage && (
              <div className="flex justify-between">
                <span className="text-gray-400">DOT:</span>
                <span className="text-orange-400">{ability.dotDamage}/sec for {ability.dotDuration}s</span>
              </div>
            )}

            {ability.aoeRadius && (
              <div className="flex justify-between">
                <span className="text-gray-400">AOE Radius:</span>
                <span className="text-blue-400">{ability.aoeRadius}</span>
              </div>
            )}

            {ability.pierceCount && ability.pierceCount > 1 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Pierce:</span>
                <span className="text-purple-400">{ability.pierceCount} enemies</span>
              </div>
            )}

            {ability.chainCount && ability.chainCount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Chain:</span>
                <span className="text-yellow-400">{ability.chainCount} targets</span>
              </div>
            )}

            <div className="flex justify-between">
              <span className="text-gray-400">Mana Cost:</span>
              <span className={canAfford ? 'text-blue-400' : 'text-red-400'}>
                {ability.manaCost} MP
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-400">Cooldown:</span>
              <span className="text-gray-300">{ability.cooldown}s</span>
            </div>

            {ability.evolutionLevel > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Evolution:</span>
                <span className="text-purple-400">Level {ability.evolutionLevel}</span>
              </div>
            )}
          </div>

          {!isReady && cooldownPercent > 0 && (
            <div className="mt-2 text-red-400 text-xs font-bold">
              Cooldown: {(cooldownPercent * ability.cooldown).toFixed(1)}s
            </div>
          )}

          {!canAfford && isReady && (
            <div className="mt-2 text-red-400 text-xs font-bold">Not Enough Mana</div>
          )}

          {!abilitySystem.getAbilityState(ability.id)?.isUnlocked && (
            <div className="mt-2 text-orange-400 text-xs font-bold">🔒 Locked</div>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 pointer-events-auto">
      <div className="flex items-end gap-6">
        <div className="flex items-end gap-2">
          {slots.map((abilityType, index) => {
            const ability = ABILITY_CONFIGS[abilityType];
            const isReady = abilitySystem.isAbilityReady(abilityType);
            const canAfford = currentMana >= ability.manaCost;
            const cooldownPercent = abilitySystem.getCooldownPercent(abilityType);
            const slotColor = getSlotColor(index);
            const isPressed = pressedSlots.has(index);
            const isUnlocked = abilitySystem.getAbilityState(abilityType)?.isUnlocked ?? false;

            return (
              <div
                key={index}
                className="relative"
                onMouseEnter={(e) => showTooltip(abilityType, e)}
                onMouseLeave={hideTooltip}
                onMouseMove={(e) => showTooltip(abilityType, e)}
              >
                {/* Keybind label */}
                <div
                  className={`
                    absolute -top-5 left-1/2 transform -translate-x-1/2
                    text-white text-xs font-bold bg-black/80 px-2 py-0.5 rounded
                    border border-gray-600
                    transition-all duration-75
                    ${isPressed ? 'scale-110 bg-white text-black' : ''}
                  `}
                >
                  {getKeyDisplay(index)}
                </div>

                {/* Ability slot */}
                <button
                  className={`
                    w-14 h-14 rounded-lg border-2 flex items-center justify-center text-2xl
                    transition-all duration-75 relative overflow-hidden
                    ${isPressed
                      ? 'scale-95 border-white brightness-110'
                      : 'hover:scale-105'
                    }
                    ${isReady && canAfford && isUnlocked
                      ? 'border-white/50 hover:border-white'
                      : 'border-gray-600 opacity-70'
                    }
                  `}
                  style={{
                    backgroundColor: slotColor + (isPressed ? '80' : '40'),
                    boxShadow: isPressed
                      ? `0 0 25px ${slotColor}, inset 0 0 15px ${slotColor}`
                      : isReady && canAfford && isUnlocked
                        ? `0 0 15px ${slotColor}60`
                        : 'none',
                  }}
                  onClick={() => triggerAbility(index + 1)}
                  onMouseDown={() => {
                    setPressedSlots(prev => new Set(prev).add(index));
                  }}
                  onMouseUp={() => {
                    setPressedSlots(prev => {
                      const newSet = new Set(prev);
                      newSet.delete(index);
                      return newSet;
                    });
                  }}
                  onMouseLeave={() => {
                    setPressedSlots(prev => {
                      const newSet = new Set(prev);
                      newSet.delete(index);
                      return newSet;
                    });
                  }}
                >
                  {/* Icon */}
                  <span className={isUnlocked ? '' : 'opacity-50 grayscale'}>
                    {ability.icon}
                  </span>

                  {/* Pressed flash effect */}
                  {isPressed && (
                    <div
                      className="absolute inset-0 bg-white/30 animate-pulse"
                    />
                  )}
                </button>

                {/* Cooldown overlay */}
                {cooldownPercent > 0 && (
                  <div
                    className="absolute inset-0 bg-black/80 rounded-lg flex items-center justify-center"
                  >
                    <span className="text-white text-xs font-bold">
                      {(cooldownPercent * ability.cooldown).toFixed(1)}s
                    </span>
                  </div>
                )}

                {/* Mana cost indicator */}
                {canAfford && cooldownPercent === 0 && isUnlocked && (
                  <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 text-blue-400 text-[10px] font-bold bg-black/60 px-1 rounded">
                    {ability.manaCost}
                  </div>
                )}

                {/* Not enough mana indicator */}
                {!canAfford && cooldownPercent === 0 && isUnlocked && (
                  <div className="absolute inset-0 bg-red-900/60 rounded-lg flex items-center justify-center">
                    <span className="text-red-400 text-lg">✕</span>
                  </div>
                )}

                {/* Locked indicator */}
                {!isUnlocked && (
                  <div className="absolute inset-0 bg-black/70 rounded-lg flex items-center justify-center">
                    <span className="text-orange-400 text-lg">🔒</span>
                  </div>
                )}

                {/* Slot number indicator */}
                <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 text-gray-500 text-[10px]">
                  {index + 1}
                </div>
              </div>
            );
          })}
        </div>

        {/* Item Slots */}
        <div className="flex items-end gap-2 border-l border-gray-700 pl-6">
          {[0, 1, 2].map((index) => {
            const item = inventory[index];
            const isPressed = pressedItems.has(index);

            return (
              <div
                key={`item-${index}`}
                className="relative"
                onMouseEnter={(e) => item && showItemTooltip(item, e)}
                onMouseLeave={hideTooltip}
              >
                {/* Keybind label */}
                <div
                  className={`
                    absolute -top-5 left-1/2 transform -translate-x-1/2
                    text-white text-[10px] font-bold bg-black/80 px-1.5 py-0.5 rounded
                    border border-gray-600
                    ${isPressed ? 'scale-110 bg-white text-black' : ''}
                  `}
                >
                  {getItemKeyDisplay(index)}
                </div>

                {/* Item slot */}
                <button
                  className={`
                    w-12 h-12 rounded-lg border-2 flex items-center justify-center text-xl
                    transition-all duration-75 relative overflow-hidden bg-gray-900/40
                    ${item ? 'border-yellow-600/50 hover:border-yellow-400' : 'border-gray-800 opacity-50'}
                    ${isPressed ? 'scale-95 border-white' : ''}
                  `}
                  onClick={() => triggerItem(index)}
                  onMouseDown={() => {
                    setPressedItems(prev => new Set(prev).add(index));
                  }}
                  onMouseUp={() => {
                    setPressedItems(prev => {
                      const newSet = new Set(prev);
                      newSet.delete(index);
                      return newSet;
                    });
                  }}
                  onMouseLeave={() => {
                    setPressedItems(prev => {
                      const newSet = new Set(prev);
                      newSet.delete(index);
                      return newSet;
                    });
                  }}
                >
                  {item ? item.icon : ''}
                  
                  {/* Pressed flash effect */}
                  {isPressed && (
                    <div
                      className="absolute inset-0 bg-white/30 animate-pulse"
                    />
                  )}
                </button>
                
                {item && (
                   <div className="absolute -bottom-2 right-0 bg-yellow-600 text-[8px] px-1 rounded-full text-white font-bold">
                      1
                   </div>
                )}

                {/* Slot number indicator */}
                <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 text-gray-500 text-[10px]">
                  {index + 6}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mana bar */}
      <div className="mt-5 w-full max-w-md mx-auto">
        <div className="flex justify-between text-xs text-blue-400 mb-1">
          <span className="font-bold">Mana</span>
          <span>{Math.floor(currentMana)} / {maxMana}</span>
        </div>
        <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden border border-gray-600">
          <div
            className="h-full bg-gradient-to-r from-blue-600 via-blue-400 to-blue-300 transition-all duration-200"
            style={{
              width: `${(currentMana / maxMana) * 100}%`,
              boxShadow: currentMana < maxMana * 0.2 ? '0 0 10px #ef4444' : 'none'
            }}
          />
        </div>
        {currentMana < 20 && (
          <div className="text-center text-red-400 text-[10px] mt-1 animate-pulse">
            Low Mana!
          </div>
        )}
      </div>

      {renderTooltip()}
    </div>
  );
};
