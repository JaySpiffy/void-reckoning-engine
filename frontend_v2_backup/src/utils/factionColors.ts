/**
 * Utility for mapping factions to their consistent UI colors.
 * Ported from legacy dashboard.js logic.
 */

export const FACTION_COLORS: Record<string, string> = {
    // Principal Factions
    'Empire': '#ef4444',        // Red
    'Rebels': '#3b82f6',        // Blue
    'Neutral': '#6b7280',       // Gray
    'Unaligned': '#9ca3af',     // Light Gray

    // Warhammer 40k Defaults (if applicable)
    'Imperium': '#f59e0b',      // Gold
    'Chaos': '#d946ef',         // Magenta/Purple
    'Orks': '#22c55e',          // Green
    'Eldar': '#06b6d4',         // Cyan
    'Necrons': '#10b981',       // Emerald
    'Tyranids': '#f43f5e',      // Rose
    'Tau': '#fbbf24',           // Amber
};

/**
 * Gets the color for a faction, with a deterministic fallback for unknown factions.
 */
export const getFactionColor = (faction: string | null | undefined): string => {
    if (!faction) return FACTION_COLORS['Neutral'];

    if (FACTION_COLORS[faction]) {
        return FACTION_COLORS[faction];
    }

    // Deterministic hash-based color fallback
    let hash = 0;
    for (let i = 0; i < faction.length; i++) {
        hash = faction.charCodeAt(i) + ((hash << 5) - hash);
    }

    const h = Math.abs(hash % 360);
    const s = 60 + (hash % 20); // 60-80%
    const l = 50 + (hash % 10); // 50-60%

    return `hsl(${h}, ${s}%, ${l}%)`;
};

/**
 * Common color constants for UI elements
 */
export const UI_COLORS = {
    lane: 'rgba(148, 163, 184, 0.1)',
    laneHighlighted: 'rgba(148, 163, 184, 0.4)',
    systemStroke: 'rgba(255, 255, 255, 0.2)',
    systemSelected: '#fff',
    battle: '#ef4444',
    capture: '#f59e0b'
};
