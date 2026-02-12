let idCounter = 0;

export function generateId(prefix: string = 'entity'): string {
  return `${prefix}_${++idCounter}_${Date.now().toString(36)}`;
}

export function resetIdCounter(): void {
  idCounter = 0;
}
