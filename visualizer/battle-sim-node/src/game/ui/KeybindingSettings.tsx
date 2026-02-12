import { useState, useEffect } from 'react';
import { keybindingSystem, BindableAction, type Keybinding } from '../systems/KeybindingSystem';

interface KeybindingSettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

interface BindingState {
  action: BindableAction;
  isListening: boolean;
}

export const KeybindingSettings = ({ isOpen, onClose }: KeybindingSettingsProps) => {
  const [bindings, setBindings] = useState<Record<BindableAction, Keybinding>>(
    keybindingSystem.getCurrentProfile().bindings
  );
  const [listeningState, setListeningState] = useState<BindingState | null>(null);
  const [conflict, setConflict] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Update bindings when opened - Handled by key-based remount in parent

  // Listen for key presses when in binding mode
  useEffect(() => {
    if (!listeningState) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const newBinding: Keybinding = {
        key: e.code,
        display: e.key.toUpperCase(),
        modifiers: {
          shift: e.shiftKey,
          ctrl: e.ctrlKey,
          alt: e.altKey,
        },
      };

      // Check for conflicts
      const existingAction = Object.entries(bindings).find(
        ([action, binding]) =>
          binding.key === newBinding.key &&
          action !== listeningState.action
      );

      if (existingAction) {
        setConflict(`This key is already bound to "${keybindingSystem.getActionDisplayName(existingAction[0] as BindableAction)}"`);
        return;
      }

      // Apply binding
      const success = keybindingSystem.setBinding(listeningState.action, newBinding);
      if (success) {
        setBindings(prev => ({
          ...prev,
          [listeningState.action]: newBinding,
        }));
        setSavedMessage(`Bound ${keybindingSystem.getActionDisplayName(listeningState.action)} to ${newBinding.display}`);
        setTimeout(() => setSavedMessage(null), 2000);
      }

      setListeningState(null);
      setConflict(null);
    };

    const handleMouseDown = (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      let keyCode: string;
      let display: string;

      switch (e.button) {
        case 0:
          keyCode = 'MouseLeft';
          display = 'LMB';
          break;
        case 1:
          keyCode = 'MouseMiddle';
          display = 'MMB';
          break;
        case 2:
          keyCode = 'MouseRight';
          display = 'RMB';
          break;
        default:
          keyCode = `Mouse${e.button}`;
          display = `M${e.button}`;
      }

      const newBinding: Keybinding = {
        key: keyCode,
        display,
      };

      // Check for conflicts
      const existingAction = Object.entries(bindings).find(
        ([action, binding]) =>
          binding.key === newBinding.key &&
          action !== listeningState.action
      );

      if (existingAction) {
        setConflict(`This button is already bound to "${keybindingSystem.getActionDisplayName(existingAction[0] as BindableAction)}"`);
        return;
      }

      const success = keybindingSystem.setBinding(listeningState.action, newBinding);
      if (success) {
        setBindings(prev => ({
          ...prev,
          [listeningState.action]: newBinding,
        }));
        setSavedMessage(`Bound ${keybindingSystem.getActionDisplayName(listeningState.action)} to ${display}`);
        setTimeout(() => setSavedMessage(null), 2000);
      }

      setListeningState(null);
      setConflict(null);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousedown', handleMouseDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousedown', handleMouseDown);
    };
  }, [listeningState, bindings]);

  const startListening = (action: BindableAction) => {
    setListeningState({ action, isListening: true });
    setConflict(null);
  };

  const cancelListening = () => {
    setListeningState(null);
    setConflict(null);
  };

  const resetBinding = (action: BindableAction) => {
    keybindingSystem.resetBinding(action);
    setBindings(keybindingSystem.getCurrentProfile().bindings);
  };

  const resetAll = () => {
    if (confirm('Reset all keybindings to default?')) {
      keybindingSystem.resetAll();
      setBindings(keybindingSystem.getCurrentProfile().bindings);
    }
  };

  const loadProfile = (profileName: 'default' | 'alternate') => {
    keybindingSystem.loadProfile(profileName);
    setBindings(keybindingSystem.getCurrentProfile().bindings);
  };

  const getActionCategory = (action: BindableAction): string => {
    if (action.includes('ABILITY')) return 'Abilities';
    if (action.includes('MOVE')) return 'Movement';
    return 'Game Controls';
  };

  const groupedActions = Object.values(BindableAction).reduce((acc, action) => {
    const category = getActionCategory(action);
    if (!acc[category]) acc[category] = [];
    acc[category].push(action);
    return acc;
  }, {} as Record<string, BindableAction[]>);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 pointer-events-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget && !listeningState) {
          onClose();
        }
      }}
    >
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-[600px] max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">Keybindings</h2>
            <p className="text-gray-400 text-sm">Click a binding to change it</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
            disabled={!!listeningState}
          >
            ✕
          </button>
        </div>

        {/* Profile Selection */}
        <div className="mb-6 p-4 bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-400 mb-2">Quick Load Profile:</div>
          <div className="flex gap-2">
            <button
              onClick={() => loadProfile('default')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-colors"
            >
              Default (1-5)
            </button>
            <button
              onClick={() => loadProfile('alternate')}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded text-sm font-medium transition-colors"
            >
              Alternate (LMB/QER)
            </button>
          </div>
        </div>

        {/* Status Messages */}
        {listeningState && (
          <div className="mb-4 p-4 bg-yellow-900/50 border border-yellow-600 rounded-lg text-center">
            <div className="text-yellow-400 font-bold text-lg animate-pulse">
              Press any key or mouse button...
            </div>
            <button
              onClick={cancelListening}
              className="mt-2 text-yellow-300 hover:text-yellow-200 text-sm underline"
            >
              Cancel
            </button>
          </div>
        )}

        {conflict && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-600 rounded-lg text-red-400 text-sm">
            ⚠️ {conflict}
          </div>
        )}

        {savedMessage && (
          <div className="mb-4 p-3 bg-green-900/50 border border-green-600 rounded-lg text-green-400 text-sm">
            ✓ {savedMessage}
          </div>
        )}

        {/* Bindings List */}
        <div className="space-y-6">
          {Object.entries(groupedActions).map(([category, actions]) => (
            <div key={category}>
              <h3 className="text-gray-400 text-sm font-bold uppercase tracking-wider mb-3">
                {category}
              </h3>
              <div className="space-y-2">
                {actions.map((action) => {
                  const binding = bindings[action];
                  const isListening = listeningState?.action === action;

                  return (
                    <div
                      key={action}
                      className={`
                        flex items-center justify-between p-3 rounded-lg transition-all
                        ${isListening
                          ? 'bg-yellow-900/30 border-2 border-yellow-500'
                          : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
                        }
                      `}
                    >
                      <span className="text-white">
                        {keybindingSystem.getActionDisplayName(action)}
                      </span>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => startListening(action)}
                          disabled={!!listeningState && listeningState.action !== action}
                          className={`
                            px-4 py-2 rounded font-mono font-bold min-w-[80px] text-center
                            transition-all
                            ${isListening
                              ? 'bg-yellow-600 text-white animate-pulse'
                              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }
                            ${listeningState && listeningState.action !== action ? 'opacity-50 cursor-not-allowed' : ''}
                          `}
                        >
                          {binding.display}
                          {binding.modifiers?.shift && ' +SHIFT'}
                          {binding.modifiers?.ctrl && ' +CTRL'}
                          {binding.modifiers?.alt && ' +ALT'}
                        </button>

                        <button
                          onClick={() => resetBinding(action)}
                          disabled={!!listeningState}
                          className="px-2 py-2 text-gray-500 hover:text-gray-300 transition-colors"
                          title="Reset to default"
                        >
                          ↺
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="mt-6 pt-4 border-t border-gray-700 flex justify-between">
          <button
            onClick={resetAll}
            disabled={!!listeningState}
            className="px-4 py-2 text-red-400 hover:text-red-300 text-sm transition-colors"
          >
            Reset All to Default
          </button>

          <button
            onClick={onClose}
            disabled={!!listeningState}
            className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-medium transition-colors"
          >
            Done
          </button>
        </div>

        {/* Tips */}
        <div className="mt-4 p-3 bg-gray-800/50 rounded text-xs text-gray-500">
          <strong>Tips:</strong> Click any binding and press a key to rebind.
          You can bind mouse buttons (LMB, RMB, MMB) too.
          Conflicts will be detected automatically.
        </div>
      </div>
    </div>
  );
};
