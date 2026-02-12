import { useState, useEffect } from 'react';
import { MUTATIONS, mutationSystem } from '../systems/MutationSystem';
import type { Mutation , MutationType} from '../systems/MutationSystem';
import { dnaSystem } from '../systems/DNASystem';
import type { DNAType} from '../types';
import { GameEvent } from '../types/events';
import { globalEvents } from '../utils';

interface MutationShopUIProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MutationShopUI = ({ isOpen, onClose }: MutationShopUIProps) => {
  const [currentMutationPoints, setCurrentMutationPoints] = useState(0);
  const [currentGenome, setCurrentGenome] = useState(dnaSystem.getGenome());
  const [selectedMutationType, setSelectedMutationType] = useState<MutationType | null>(null);
  const [selectedDnaTarget, setSelectedDnaTarget] = useState<DNAType | null>(null);

  useEffect(() => {
    const updatePoints = () => {
      setCurrentMutationPoints(dnaSystem.getMutationPoints());
      setCurrentGenome(dnaSystem.getGenome());
    };

    globalEvents.on(GameEvent.MUTATION_APPLIED, updatePoints);
    // There isn't a direct event for mutation points gain, so we'll poll for now or add an event
    // For simplicity, we'll just update on panel open and mutation applied
    updatePoints(); 

    return () => {
      globalEvents.off(GameEvent.MUTATION_APPLIED, updatePoints);
    };
  }, [isOpen]);

  const handleApplyMutation = (mutation: Mutation) => {
    let actualTargetDna: DNAType | undefined = undefined;

    // For mutations requiring a specific DNA type, use the selected one
    if (mutation.effect.stabilityIncrease || mutation.effect.resistanceIncrease || mutation.effect.weaknessReduce) {
      if (!selectedDnaTarget) {
        alert('Please select a DNA type to apply this mutation.');
        return;
      }
      actualTargetDna = selectedDnaTarget;
    }

    const success = mutationSystem.applyMutation(mutation.id, actualTargetDna);
    if (success) {
      // Refresh local state
      setCurrentMutationPoints(dnaSystem.getMutationPoints());
      setCurrentGenome(dnaSystem.getGenome());
      setSelectedMutationType(null); // Clear selection
      setSelectedDnaTarget(null);
    }
  };

  if (!isOpen) return null;

  const dnaTypes = Array.from(currentGenome.strands.keys()).sort();

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 pointer-events-auto">
      <div className="bg-gray-900 rounded-xl border border-gray-700 max-w-4xl w-full max-h-[90vh] overflow-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">🧬 Genetic Mutation Shop</h2>
            <p className="text-gray-400 text-sm">Spend Mutation Points to alter your genome</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">✕</button>
        </div>

        {/* Mutation Points */}
        <div className="mb-6 p-4 bg-purple-900/30 rounded-lg border border-purple-700 flex justify-between items-center">
          <div className="text-purple-400 text-sm mb-1 uppercase tracking-wider">Your Mutation Points:</div>
          <div className="text-white text-3xl font-bold">{currentMutationPoints} MP</div>
        </div>

        {/* Current Genome Overview (Optional, for context) */}
        <div className="mb-6 p-4 bg-black/40 rounded-lg border border-gray-800">
          <div className="text-gray-400 text-sm mb-2">Current DNA Breakdown:</div>
          <div className="grid grid-cols-4 gap-2 text-sm">
            {dnaTypes.map((type) => (
              <div key={type} className="flex items-center gap-1 capitalize">
                <span className="text-gray-400">{type}:</span>
                <span className="text-white font-semibold">{currentGenome.strands.get(type)?.value.toFixed(0) || '0'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Mutation List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.values(MUTATIONS).map((mutation) => (
            <div 
              key={mutation.id} 
              className={`p-4 rounded-lg border transition-all flex flex-col justify-between
                ${selectedMutationType === mutation.id ? 'bg-blue-900/40 border-blue-500' : 'bg-black/40 border-gray-700'}
              `}
            >
              <div>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-bold text-white">{mutation.name}</h3>
                  <span className="text-yellow-400 font-bold">{mutation.cost} MP</span>
                </div>
                <p className="text-gray-300 text-sm">{mutation.description}</p>

                {/* Specific DNA target selection */}
                {(mutation.effect.stabilityIncrease || mutation.effect.resistanceIncrease || mutation.effect.weaknessReduce) && (
                  <div className="mt-3">
                    <label htmlFor={`dna-target-${mutation.id}`} className="block text-gray-400 text-xs mb-1">Target DNA Type:</label>
                    <select
                      id={`dna-target-${mutation.id}`}
                      className="w-full p-2 rounded bg-gray-700 text-white border border-gray-600 capitalize"
                      value={selectedDnaTarget || ''}
                      onChange={(e) => setSelectedDnaTarget(e.target.value as DNAType)}
                      onClick={() => setSelectedMutationType(mutation.id)} // Select this mutation when dropdown is clicked
                    >
                      <option value="">Select a DNA Type</option>
                      {dnaTypes.map(type => (
                        <option key={type} value={type} className="capitalize">{type}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              
              <button
                onClick={() => handleApplyMutation(mutation)}
                disabled={currentMutationPoints < mutation.cost || Boolean((mutation.effect.stabilityIncrease || mutation.effect.resistanceIncrease || mutation.effect.weaknessReduce) && !selectedDnaTarget) }
                className={`mt-4 w-full px-4 py-2 rounded-lg font-bold transition-colors
                  ${currentMutationPoints >= mutation.cost && Boolean(!(mutation.effect.stabilityIncrease || mutation.effect.resistanceIncrease || mutation.effect.weaknessReduce) || selectedDnaTarget)
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                Apply Mutation
              </button>
            </div>
          ))}
        </div>

        {/* Close button */}
        <div className="mt-6 text-center">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
