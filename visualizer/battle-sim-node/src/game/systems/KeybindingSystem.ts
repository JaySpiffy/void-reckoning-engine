/**
 * KEYBINDING SYSTEM - Comprehensive Input Management
 *
 * Features:
 * - Customizable keybindings for all abilities
 * - Multiple binding profiles (default, alternate, custom)
 * - Visual key display on action bar
 * - Key press visualization (pressed state)
 * - Persistence to localStorage
 * - Conflict detection
 * - Modifier key support (Shift, Ctrl, Alt)
 */

import { logger, LogCategory } from '../managers/LogManager';
import { globalEvents } from '../utils';
import { GameEvent } from '../types';

// Action types that can be bound to keys
export enum BindableAction {
  // Ability slots
  ABILITY_SLOT_1 = 'ability_slot_1',
  ABILITY_SLOT_2 = 'ability_slot_2',
  ABILITY_SLOT_3 = 'ability_slot_3',
  ABILITY_SLOT_4 = 'ability_slot_4',
  ABILITY_SLOT_5 = 'ability_slot_5',

  // Movement
  MOVE_UP = 'move_up',
  MOVE_DOWN = 'move_down',
  MOVE_LEFT = 'move_left',
  MOVE_RIGHT = 'move_right',

  // Game controls
  PAUSE = 'pause',
  INTERACT = 'interact',
  OPEN_EVOLUTION = 'open_evolution',
  OPEN_INVENTORY = 'open_inventory',
  OPEN_MUTATION_SHOP = 'open_mutation_shop',
  TOGGLE_BUILD_MODE = 'toggle_build_mode',

  // Items
  USE_ITEM_1 = 'use_item_1',
  USE_ITEM_2 = 'use_item_2',
  USE_ITEM_3 = 'use_item_3',

  // Debug
  TOGGLE_DEBUG = 'toggle_debug',
}

// Keybinding configuration
export interface Keybinding {
  key: string;           // The key code (e.g., 'KeyW', 'Digit1', 'Space')
  display: string;       // Display text (e.g., 'W', '1', 'SPACE')
  modifiers?: {
    shift?: boolean;
    ctrl?: boolean;
    alt?: boolean;
  };
}

// Complete keybinding profile
export interface KeybindingProfile {
  name: string;
  description: string;
  bindings: Record<BindableAction, Keybinding>;
}

// Event data for key press visualization
export interface KeyPressEvent {
  action: BindableAction;
  pressed: boolean;
}

// Default QWERTY keybindings
const DEFAULT_BINDINGS: Record<BindableAction, Keybinding> = {
  [BindableAction.ABILITY_SLOT_1]: { key: 'Digit1', display: '1' },
  [BindableAction.ABILITY_SLOT_2]: { key: 'Digit2', display: '2' },
  [BindableAction.ABILITY_SLOT_3]: { key: 'Digit3', display: '3' },
  [BindableAction.ABILITY_SLOT_4]: { key: 'Digit4', display: '4' },
  [BindableAction.ABILITY_SLOT_5]: { key: 'Digit5', display: '5' },
  [BindableAction.MOVE_UP]: { key: 'KeyW', display: 'W' },
  [BindableAction.MOVE_DOWN]: { key: 'KeyS', display: 'S' },
  [BindableAction.MOVE_LEFT]: { key: 'KeyA', display: 'A' },
  [BindableAction.MOVE_RIGHT]: { key: 'KeyD', display: 'D' },
  [BindableAction.PAUSE]: { key: 'Escape', display: 'ESC' },
  [BindableAction.INTERACT]: { key: 'KeyF', display: 'F' },
  [BindableAction.OPEN_EVOLUTION]: { key: 'KeyT', display: 'T' },
  [BindableAction.OPEN_INVENTORY]: { key: 'KeyI', display: 'I' },
  [BindableAction.OPEN_MUTATION_SHOP]: { key: 'KeyM', display: 'M' },
  [BindableAction.TOGGLE_BUILD_MODE]: { key: 'KeyB', display: 'B' },
  [BindableAction.USE_ITEM_1]: { key: 'Digit6', display: '6' },
  [BindableAction.USE_ITEM_2]: { key: 'Digit7', display: '7' },
  [BindableAction.USE_ITEM_3]: { key: 'Digit8', display: '8' },
  [BindableAction.TOGGLE_DEBUG]: { key: 'Backquote', display: '`' },
};

// Alternative keybindings (WASD + Mouse focus)
const ALTERNATE_BINDINGS: Record<BindableAction, Keybinding> = {
  [BindableAction.ABILITY_SLOT_1]: { key: 'MouseLeft', display: 'LMB' },
  [BindableAction.ABILITY_SLOT_2]: { key: 'Space', display: 'SPACE' },
  [BindableAction.ABILITY_SLOT_3]: { key: 'KeyQ', display: 'Q' },
  [BindableAction.ABILITY_SLOT_4]: { key: 'KeyE', display: 'E' },
  [BindableAction.ABILITY_SLOT_5]: { key: 'KeyR', display: 'R' },
  [BindableAction.MOVE_UP]: { key: 'KeyW', display: 'W' },
  [BindableAction.MOVE_DOWN]: { key: 'KeyS', display: 'S' },
  [BindableAction.MOVE_LEFT]: { key: 'KeyA', display: 'A' },
  [BindableAction.MOVE_RIGHT]: { key: 'KeyD', display: 'D' },
  [BindableAction.PAUSE]: { key: 'Escape', display: 'ESC' },
  [BindableAction.INTERACT]: { key: 'KeyF', display: 'F' },
  [BindableAction.OPEN_EVOLUTION]: { key: 'KeyT', display: 'T' },
  [BindableAction.OPEN_INVENTORY]: { key: 'KeyI', display: 'I' },
  [BindableAction.OPEN_MUTATION_SHOP]: { key: 'KeyM', display: 'M' },
  [BindableAction.TOGGLE_BUILD_MODE]: { key: 'KeyB', display: 'B' },
  [BindableAction.USE_ITEM_1]: { key: 'Digit6', display: '6' },
  [BindableAction.USE_ITEM_2]: { key: 'Digit7', display: '7' },
  [BindableAction.USE_ITEM_3]: { key: 'Digit8', display: '8' },
  [BindableAction.TOGGLE_DEBUG]: { key: 'Backquote', display: '`' },
};

// Predefined profiles
export const KEYBINDING_PROFILES: Record<string, KeybindingProfile> = {
  default: {
    name: 'Default',
    description: 'Standard 1-5 ability keys with WASD movement',
    bindings: DEFAULT_BINDINGS,
  },
  alternate: {
    name: 'Alternate',
    description: 'LMB for basic attack, QER for abilities',
    bindings: ALTERNATE_BINDINGS,
  },
};

// Storage key for localStorage
const STORAGE_KEY = 'darwins-island-keybindings';

export class KeybindingSystem {
  private currentBindings: Record<BindableAction, Keybinding> = { ...DEFAULT_BINDINGS };
  private pressedKeys: Set<string> = new Set();
  private pressedActions: Set<BindableAction> = new Set();
  private isListening: boolean = false;
  private customProfileName: string = 'Custom';

  constructor() {
    this.loadFromStorage();
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Keyboard events
    window.addEventListener('keydown', this.handleKeyDown);
    window.addEventListener('keyup', this.handleKeyUp);

    // Mouse events for mouse bindings
    window.addEventListener('mousedown', this.handleMouseDown);
    window.addEventListener('mouseup', this.handleMouseUp);

    // Prevent context menu on right click (for potential right-click abilities)
    window.addEventListener('contextmenu', (e) => {
      if (this.isListening) {
        e.preventDefault();
      }
    });
  }

  private handleKeyDown = (e: KeyboardEvent): void => {
    if (!this.isListening) return;

    const keyCode = e.code;
    this.pressedKeys.add(keyCode);

    // Find action bound to this key
    const action = this.getActionForKey(keyCode);
    if (action) {
      this.pressedActions.add(action);
      this.emitKeyPress(action, true);
    }
  };

  private handleKeyUp = (e: KeyboardEvent): void => {
    const keyCode = e.code;
    this.pressedKeys.delete(keyCode);

    const action = this.getActionForKey(keyCode);
    if (action) {
      this.pressedActions.delete(action);
      this.emitKeyPress(action, false);
    }
  };

  private handleMouseDown = (e: MouseEvent): void => {
    if (!this.isListening) return;

    const mouseCode = this.getMouseButtonCode(e.button);
    this.pressedKeys.add(mouseCode);

    const action = this.getActionForKey(mouseCode);
    if (action) {
      this.pressedActions.add(action);
      this.emitKeyPress(action, true);
    }
  };

  private handleMouseUp = (e: MouseEvent): void => {
    const mouseCode = this.getMouseButtonCode(e.button);
    this.pressedKeys.delete(mouseCode);

    const action = this.getActionForKey(mouseCode);
    if (action) {
      this.pressedActions.delete(action);
      this.emitKeyPress(action, false);
    }
  };

  private getMouseButtonCode(button: number): string {
    switch (button) {
      case 0: return 'MouseLeft';
      case 1: return 'MouseMiddle';
      case 2: return 'MouseRight';
      default: return `Mouse${button}`;
    }
  }

  private emitKeyPress(action: BindableAction, pressed: boolean): void {
    globalEvents.emit(GameEvent.KEYBINDING_PRESSED, { action, pressed } as KeyPressEvent);
  }

  private getActionForKey(keyCode: string): BindableAction | null {
    for (const [action, binding] of Object.entries(this.currentBindings)) {
      if (binding.key === keyCode) {
        return action as BindableAction;
      }
    }
    return null;
  }

  // Start/stop listening for input
  startListening(): void {
    this.isListening = true;
    this.pressedKeys.clear();
    this.pressedActions.clear();
  }

  stopListening(): void {
    this.isListening = false;
    this.pressedKeys.clear();
    this.pressedActions.clear();
  }

  // Check if an action is currently pressed
  isActionPressed(action: BindableAction): boolean {
    return this.pressedActions.has(action);
  }

  // Check if a specific key is pressed
  isKeyPressed(keyCode: string): boolean {
    return this.pressedKeys.has(keyCode);
  }

  // Get the binding for an action
  getBinding(action: BindableAction): Keybinding {
    return this.currentBindings[action];
  }

  // Get display text for an action's key
  getKeyDisplay(action: BindableAction): string {
    return this.currentBindings[action]?.display || '?';
  }

  // Set a custom binding
  setBinding(action: BindableAction, binding: Keybinding): boolean {
    // Check for conflicts
    const conflictingAction = this.getActionForKey(binding.key);
    if (conflictingAction && conflictingAction !== action) {
      logger.warn(LogCategory.KEYBINDING, `Conflict: ${binding.key} is already bound to ${conflictingAction}`);
      return false;
    }

    this.currentBindings[action] = binding;
    this.saveToStorage();
    return true;
  }

  // Reset to default profile
  loadProfile(profileName: 'default' | 'alternate'): void {
    const profile = KEYBINDING_PROFILES[profileName];
    if (profile) {
      this.currentBindings = { ...profile.bindings };
      this.saveToStorage();
      logger.info(LogCategory.KEYBINDING, `Loaded profile: ${profile.name}`);
    }
  }

  // Reset a single action to default
  resetBinding(action: BindableAction): void {
    this.currentBindings[action] = DEFAULT_BINDINGS[action];
    this.saveToStorage();
  }

  // Reset all to default
  resetAll(): void {
    this.currentBindings = { ...DEFAULT_BINDINGS };
    this.saveToStorage();
  }

  // Get all available actions
  getAllActions(): BindableAction[] {
    return Object.values(BindableAction);
  }

  // Get action display name
  getActionDisplayName(action: BindableAction): string {
    const names: Record<BindableAction, string> = {
      [BindableAction.ABILITY_SLOT_1]: 'Basic Attack (Slot 1)',
      [BindableAction.ABILITY_SLOT_2]: 'Dash (Slot 2)',
      [BindableAction.ABILITY_SLOT_3]: 'Primary Ability (Slot 3)',
      [BindableAction.ABILITY_SLOT_4]: 'Secondary Ability (Slot 4)',
      [BindableAction.ABILITY_SLOT_5]: 'Ultimate (Slot 5)',
      [BindableAction.MOVE_UP]: 'Move Up',
      [BindableAction.MOVE_DOWN]: 'Move Down',
      [BindableAction.MOVE_LEFT]: 'Move Left',
      [BindableAction.MOVE_RIGHT]: 'Move Right',
      [BindableAction.PAUSE]: 'Pause Game',
      [BindableAction.INTERACT]: 'Interact',
      [BindableAction.OPEN_EVOLUTION]: 'Open Evolution Panel',
      [BindableAction.OPEN_INVENTORY]: 'Open Inventory',
      [BindableAction.OPEN_MUTATION_SHOP]: 'Open Mutation Shop',
      [BindableAction.TOGGLE_BUILD_MODE]: 'Toggle Build Mode',
      [BindableAction.USE_ITEM_1]: 'Use Item Slot 1',
      [BindableAction.USE_ITEM_2]: 'Use Item Slot 2',
      [BindableAction.USE_ITEM_3]: 'Use Item Slot 3',
      [BindableAction.TOGGLE_DEBUG]: 'Toggle Debug Panel',
    };
    return names[action] || action;
  }

  // Get ability slot from action
  getAbilitySlot(action: BindableAction): number | null {
    switch (action) {
      case BindableAction.ABILITY_SLOT_1: return 1;
      case BindableAction.ABILITY_SLOT_2: return 2;
      case BindableAction.ABILITY_SLOT_3: return 3;
      case BindableAction.ABILITY_SLOT_4: return 4;
      case BindableAction.ABILITY_SLOT_5: return 5;
      default: return null;
    }
  }

  // Check if action is an ability slot
  isAbilityAction(action: BindableAction): boolean {
    return action.startsWith('ability_slot_');
  }

  // Save to localStorage
  private saveToStorage(): void {
    try {
      const data = {
        bindings: this.currentBindings,
        profileName: this.customProfileName,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      logger.warn(LogCategory.KEYBINDING, 'Failed to save to storage', e);
    }
  }

  // Load from localStorage
  private loadFromStorage(): void {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        if (data.bindings) {
          this.currentBindings = { ...DEFAULT_BINDINGS, ...data.bindings };
          this.customProfileName = data.profileName || 'Custom';
          logger.info(LogCategory.KEYBINDING, 'Loaded custom bindings from storage');
        }
      }
    } catch (e) {
      logger.warn(LogCategory.KEYBINDING, 'Failed to load from storage', e);
    }
  }

  // Export bindings as JSON
  exportBindings(): string {
    return JSON.stringify(this.currentBindings, null, 2);
  }

  // Import bindings from JSON
  importBindings(json: string): boolean {
    try {
      const bindings = JSON.parse(json);
      // Validate
      for (const action of Object.values(BindableAction)) {
        if (!bindings[action] || !bindings[action].key || !bindings[action].display) {
          logger.error(LogCategory.KEYBINDING, `Invalid binding for ${action}`);
          return false;
        }
      }
      this.currentBindings = bindings;
      this.saveToStorage();
      return true;
    } catch (e) {
      logger.error(LogCategory.KEYBINDING, 'Failed to import bindings', e);
      return false;
    }
  }

  // Get current profile info
  getCurrentProfile(): { name: string; bindings: Record<BindableAction, Keybinding> } {
    return {
      name: this.customProfileName,
      bindings: { ...this.currentBindings },
    };
  }

  // Cleanup
  destroy(): void {
    window.removeEventListener('keydown', this.handleKeyDown);
    window.removeEventListener('keyup', this.handleKeyUp);
    window.removeEventListener('mousedown', this.handleMouseDown);
    window.removeEventListener('mouseup', this.handleMouseUp);
  }
}

// Singleton instance
export const keybindingSystem = new KeybindingSystem();
