import type { GameEventData } from '../types';

type EventCallback<T extends keyof GameEventData> = (data: GameEventData[T]) => void;

export class EventEmitter {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private listeners: Map<keyof GameEventData, Set<EventCallback<any>>> = new Map();

  on<T extends keyof GameEventData>(event: T, callback: EventCallback<T>): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    return () => this.off(event, callback);
  }

  off<T extends keyof GameEventData>(event: T, callback: EventCallback<T>): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  emit<T extends keyof GameEventData>(event: T, data: GameEventData[T]): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  once<T extends keyof GameEventData>(event: T, callback: EventCallback<T>): void {
    const onceCallback = (data: GameEventData[T]) => {
      this.off(event, onceCallback);
      callback(data);
    };
    this.on(event, onceCallback);
  }

  clear(): void {
    this.listeners.clear();
  }
}

export const globalEvents = new EventEmitter();
