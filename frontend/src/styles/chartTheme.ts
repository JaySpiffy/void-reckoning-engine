export const CHART_COLORS = {
    primary: '#3b82f6', // Blue
    secondary: '#8b5cf6', // Violet
    success: '#22c55e', // Green
    warning: '#f59e0b', // Amber
    danger: '#ef4444', // Red
    info: '#06b6d4', // Cyan
    neutral: '#94a3b8', // Slate
    grid: '#334155',
    text: '#94a3b8',
    tooltipBg: 'rgba(30, 41, 59, 0.95)',
    tooltipBorder: '#334155'
};

export const FACTION_COLORS: Record<string, string> = {
    // Eternal Crusade Factions
    'Solar_Hegemony': '#F59E0B',   // Amber/Gold
    'Void_Corsairs': '#8B5CF6',    // Violet
    'Zealot_Legions': '#EF4444',   // Red
    'Ascended_Order': '#06B6D4',   // Cyan
    'Hive_Swarm': '#84CC16',       // Lime
    'Iron_Vanguard': '#64748B',    // Slate
    'Rift_Daemons': '#B91C1C',     // Dark Red
    'Scavenger_Clans': '#F97316',  // Orange
    'Ancient_Guardians': '#10B981',// Emerald
    'Cyber_Synod': '#3B82F6',      // Blue

    // Generic Fallbacks
    'Player': '#3b82f6',
    'AI_1': '#ef4444',
    'AI_2': '#f59e0b',
    'AI_3': '#22c55e',
    'Neutral': '#94a3b8'
};

export const getFactionColor = (key: string): string => {
    // normalize key for matching
    const normalizedKey = key.toUpperCase();

    // Helper to find case-insensitive match in FACTION_COLORS
    const findColor = (checkKey: string): string | undefined => {
        for (const fKey in FACTION_COLORS) {
            if (fKey.toUpperCase() === checkKey) {
                return FACTION_COLORS[fKey];
            }
        }
        return undefined;
    };

    // 1. Direct Match
    let color = findColor(normalizedKey);
    if (color) return color;

    // 2. Strip Suffixes
    const suffixes = ['_PROFIT', '_STOCKPILE', '_VELOCITY', '_EFFICIENCY', '_IDLE', '_TOTAL'];
    for (const suffix of suffixes) {
        if (normalizedKey.endsWith(suffix)) {
            const base = normalizedKey.replace(suffix, '');
            color = findColor(base);
            if (color) return color;
        }
    }

    // 3. Fallback: Deterministic Hash (Ported from factionColors.ts)
    // This ensures even unknown factions get distinct, consistent colors
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
        hash = key.charCodeAt(i) + ((hash << 5) - hash);
    }
    const h = Math.abs(hash % 360);
    const s = 60 + (hash % 20); // 60-80%
    const l = 50 + (hash % 10); // 50-60%
    return `hsl(${h}, ${s}%, ${l}%)`;
};

export const chartConfig = {
    fontSize: 12,
    fontFamily: 'Inter, system-ui, sans-serif',
    gridDashArray: '3 3',
    margin: { top: 10, right: 10, left: 0, bottom: 0 },
    animationDuration: 300
};
