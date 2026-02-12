import type { InputState, Vector2 } from '../types';
import { logger, LogCategory } from '../managers/LogManager';

/**
 * INPUT SYSTEM - Captures all user input
 *
 * This system captures keyboard and mouse input and prevents
 * default browser behavior for game keys.
 */

export class InputSystem {
  private state: InputState = {
    keys: new Set(),
    mousePosition: { x: 0, y: 0 },
    mouseDown: false,
    mouseJustPressed: false,
  };

  private canvas: HTMLCanvasElement | null = null;
  private keyJustPressed: Set<string> = new Set();
  private mouseJustPressedFlag: boolean = false;
  private isInitialized: boolean = false;

  initialize(canvas: HTMLCanvasElement): void {
    if (this.isInitialized) return;

    this.canvas = canvas;

    // Keyboard events - capture on window to ensure we get all keys
    window.addEventListener('keydown', this.handleKeyDown, true);
    window.addEventListener('keyup', this.handleKeyUp, true);

    // Mouse events
    canvas.addEventListener('mousedown', this.handleMouseDown);
    canvas.addEventListener('mouseup', this.handleMouseUp);
    canvas.addEventListener('mousemove', this.handleMouseMove);
    canvas.addEventListener('mouseenter', this.handleMouseEnter);
    canvas.addEventListener('mouseleave', this.handleMouseLeave);
    canvas.addEventListener('contextmenu', this.handleContextMenu);

    // Prevent text selection and other unwanted behaviors
    if (canvas.style) {
      canvas.style.userSelect = 'none';
      (canvas.style as unknown as { webkitUserSelect: string }).webkitUserSelect = 'none';
    }

    // Focus the canvas to capture input immediately
    canvas.focus();
    canvas.tabIndex = 0;

    this.isInitialized = true;
  }

  cleanup(): void {
    window.removeEventListener('keydown', this.handleKeyDown, true);
    window.removeEventListener('keyup', this.handleKeyUp, true);

    if (this.canvas) {
      this.canvas.removeEventListener('mousedown', this.handleMouseDown);
      this.canvas.removeEventListener('mouseup', this.handleMouseUp);
      this.canvas.removeEventListener('mousemove', this.handleMouseMove);
      this.canvas.removeEventListener('mouseenter', this.handleMouseEnter);
      this.canvas.removeEventListener('mouseleave', this.handleMouseLeave);
      this.canvas.removeEventListener('contextmenu', this.handleContextMenu);
    }
  }

  update(): void {
    // Clear just-pressed states
    this.keyJustPressed.clear();
    this.state.mouseJustPressed = this.mouseJustPressedFlag;
    this.mouseJustPressedFlag = false;
  }

  private handleKeyDown = (e: KeyboardEvent): void => {
    const key = e.key.toLowerCase();

    // Prevent default for game keys to stop page scrolling
    const gameKeys = ['w', 'a', 's', 'd', ' ', 'enter', 'escape', 'p', '1', '2', '3', '4', '5', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'];
    if (gameKeys.includes(key)) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!this.state.keys.has(key)) {
      // Log interaction
      if (['f9', 'escape', 'enter'].includes(key)) {
        logger.info(LogCategory.INPUT, `Action Key Pressed: ${key}`);
      } else {
        logger.debug(LogCategory.INPUT, `Key Down: ${key}`);
      }

      this.state.keys.add(key);
      this.keyJustPressed.add(key);
    }
  };

  private handleKeyUp = (e: KeyboardEvent): void => {
    const key = e.key.toLowerCase();
    this.state.keys.delete(key);
  };

  private handleMouseMove = (e: MouseEvent): void => {
    if (!this.canvas) return;

    const rect = this.canvas.getBoundingClientRect();
    this.state.mousePosition = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  private handleMouseDown = (e: MouseEvent): void => {
    e.preventDefault();
    this.state.mouseDown = true;
    this.mouseJustPressedFlag = true;
  };

  private handleMouseUp = (e: MouseEvent): void => {
    e.preventDefault();
    this.state.mouseDown = false;
  };

  private handleMouseEnter = (): void => {
    // Canvas regained focus
  };

  private handleMouseLeave = (): void => {
    // Mouse left canvas - release all keys to prevent stuck keys
    this.state.mouseDown = false;
  };

  private handleContextMenu = (e: Event): boolean => {
    e.preventDefault();
    return false;
  };

  // Query methods
  isKeyDown(key: string): boolean {
    return this.state.keys.has(key.toLowerCase());
  }

  isKeyJustPressed(key: string): boolean {
    return this.keyJustPressed.has(key.toLowerCase());
  }

  isAnyKeyDown(keys: string[]): boolean {
    return keys.some(key => this.isKeyDown(key));
  }

  areAllKeysDown(keys: string[]): boolean {
    return keys.every(key => this.isKeyDown(key));
  }

  getMovementVector(): Vector2 {
    let x = 0;
    let y = 0;

    if (this.isKeyDown('w') || this.isKeyDown('arrowup')) y -= 1;
    if (this.isKeyDown('s') || this.isKeyDown('arrowdown')) y += 1;
    if (this.isKeyDown('a') || this.isKeyDown('arrowleft')) x -= 1;
    if (this.isKeyDown('d') || this.isKeyDown('arrowright')) x += 1;

    return { x, y };
  }

  getMousePosition(): Vector2 {
    return { ...this.state.mousePosition };
  }

  isMouseDown(): boolean {
    return this.state.mouseDown;
  }

  isMouseJustPressed(): boolean {
    return this.state.mouseJustPressed;
  }

  getState(): InputState {
    return {
      keys: new Set(this.state.keys),
      mousePosition: { ...this.state.mousePosition },
      mouseDown: this.state.mouseDown,
      mouseJustPressed: this.state.mouseJustPressed,
    };
  }
}

export const inputSystem = new InputSystem();
