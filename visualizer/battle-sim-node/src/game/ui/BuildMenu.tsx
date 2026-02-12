import { Hammer } from 'lucide-react';
import { BuildingType, type Resources } from '../types';
import { buildingSystem, BUILDING_ARCHETYPES } from '../systems/BuildingSystem';
import { Panel, Card, Button } from './components';

interface BuildMenuProps {
  isOpen: boolean;
  onClose: () => void;
  resources: Resources;
  onSelect: (type: BuildingType) => void;
}

export const BuildMenu = ({ isOpen, onClose, resources, onSelect }: BuildMenuProps) => {
  const buildingTypes = Object.values(BuildingType);

  const handleSelect = (type: BuildingType) => {
    onSelect(type);
    onClose();
  };

  return (
    <Panel
      isOpen={isOpen}
      onClose={onClose}
      title="🏗️ Build Structures"
      size="lg"
      footer={
        <span className="text-slate-400 text-sm">
          Click a structure to enter placement mode
        </span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {buildingTypes.map((type) => {
          const arch = BUILDING_ARCHETYPES[type];
          const canAfford = buildingSystem.canAfford(type, resources);

          return (
            <Card
              key={type}
              className={`transition-all duration-200 ${
                canAfford
                  ? 'hover:border-violet-500/50 hover:shadow-lg hover:shadow-violet-900/10 cursor-pointer'
                  : 'opacity-60'
              }`}
              onClick={() => canAfford && handleSelect(type)}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center text-2xl flex-shrink-0">
                  {arch.icon}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-white capitalize truncate">
                    {type.replace(/_/g, ' ')}
                  </h4>
                  <p className="text-sm text-slate-400 mt-0.5 line-clamp-2">
                    {arch.description}
                  </p>

                  {/* Cost */}
                  <div className="flex flex-wrap gap-2 mt-3">
                    {Object.entries(arch.cost).map(([res, amount]) => {
                      const resourceKey = res.toLowerCase() as keyof Resources;
                      const currentAmount = resources[resourceKey] ?? 0;
                      const hasEnough = currentAmount >= (amount as number);
                      return (
                        <span
                          key={res}
                          className={`text-xs px-2 py-1 rounded-full ${
                            hasEnough
                              ? 'bg-green-900/30 text-green-400 border border-green-700/50'
                              : 'bg-red-900/30 text-red-400 border border-red-700/50'
                          }`}
                        >
                          {amount} {res.charAt(0).toUpperCase() + res.slice(1)}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* Build Button */}
                <Button
                  variant={canAfford ? 'default' : 'secondary'}
                  size="sm"
                  disabled={!canAfford}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelect(type);
                  }}
                  leftIcon={<Hammer className="w-4 h-4" />}
                >
                  Build
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </Panel>
  );
};
