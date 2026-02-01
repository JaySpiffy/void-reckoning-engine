import { TelemetryEvent } from '../types';
import { getFactionColor } from './factionColors';

/**
 * Generates a human-readable message from a telemetry event.
 */
export const formatEventMessage = (event: TelemetryEvent): string => {
    const data = event.data || {};
    const faction = event.faction || 'Neutral';
    const system = data.system || data.planet || 'Unknown Sector';

    switch (event.category) {
        case 'combat':
            if (event.event_type === 'battle_resolved') {
                const attacker = data.attacker || 'Attacker';
                const defender = data.defender || 'Defender';
                const winner = data.winner || 'Undetermined';
                return `Battle in ${system}: ${attacker} vs ${defender} - ${winner} Victorious`;
            }
            return `Combat activity detected in ${system}`;

        case 'economy':
            if (event.event_type === 'income_collected') {
                const amount = data.amount || 0;
                const resource = data.resource || 'Resources';
                return `${faction} collected ${amount} ${resource} from ${system}`;
            }
            return `${faction} engaged in economic activity`;

        case 'technology':
            if (event.event_type === 'tech_unlocked' || event.event_type === 'tech_event') {
                const techName = data.tech || data.technology || 'Advanced Research';
                const cost = data.cost ? ` (Cost: ${data.cost})` : '';
                return `${faction} unlocked ${techName}${cost}`;
            }
            return `${faction} made a scientific breakthrough`;

        case 'construction':
            if (event.event_type === 'construction_complete' || event.event_type === 'unit_built') {
                const object = data.building || data.unit || 'Infrastructure';
                return `${faction} completed ${object} on ${system}`;
            }
            return `${faction} started a construction project`;

        case 'system':
            if (event.event_type === 'planet_captured' || event.event_type === 'planet_update') {
                return `${system} status updated for ${faction}`;
            }
            return `System update for ${system}`;

        case 'diplomacy':
            if (event.event_type === 'treaty_signed') {
                const partner = data.partner || 'Unknown';
                return `${faction} signed a treaty with ${partner}`;
            }
            return `${faction} engaged in diplomatic activity`;

        case 'movement':
            if (event.event_type === 'movement_started') {
                const from = data.from || 'Unknown';
                const to = data.to || 'Unknown';
                const unit = data.unit || 'Unit';
                return `${faction} moved ${unit} from ${from} to ${to}`;
            }
            return `${faction} fleet movement detected`;

        case 'campaign':
            if (event.event_type === 'campaign_started') {
                return `Campaign started: ${data.campaign_name || 'New Campaign'}`;
            }
            if (event.event_type === 'turn_status') {
                return `Turn ${data.turn || '?'} - ${data.phase || 'Processing'}`;
            }
            return `Campaign event: ${event.event_type}`;

        case 'strategy':
            if (event.event_type === 'strategy_changed') {
                const strategy = data.strategy || 'Unknown Strategy';
                return `${faction} adopted ${strategy}`;
            }
            return `${faction} strategic decision made`;

        case 'doctrine':
            if (event.event_type === 'doctrine_unlocked') {
                const doctrine = data.doctrine || 'Unknown Doctrine';
                return `${faction} unlocked doctrine: ${doctrine}`;
            }
            return `${faction} doctrine event`;

        default:
            return `${event.event_type.replace(/_/g, ' ')} for ${faction}`;
    }
};

/**
 * Returns an appropriate icon and color for an event type/category.
 */
export const getEventIcon = (eventType: string, category: string): { icon: string; color: string } => {
    const categoryColors: Record<string, string> = {
        combat: '#ff4444',
        economy: '#00c851',
        technology: '#33b5e5',
        construction: '#ffbb33',
        system: '#aa66cc',
        diplomacy: '#2bbbad',
        movement: '#ff8800',
        campaign: '#9c27b0',
        strategy: '#795548',
        doctrine: '#607d8b'
    };

    const icons: Record<string, string> = {
        combat: '⚔️',
        economy: '💰',
        technology: '🔬',
        construction: '🏗️',
        system: '🌍',
        diplomacy: '🤝',
        movement: '🚀',
        campaign: '📜',
        strategy: '🎯',
        doctrine: '📖'
    };

    return {
        icon: icons[category] || '🔔',
        color: categoryColors[category] || '#8892b0'
    };
};

/**
 * Formats event time.
 */
export const formatEventTime = (timestamp: number, turn: number | null): string => {
    if (turn !== null) return `Turn ${turn}`;

    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

/**
 * Assigns priority for sorting.
 */
export const getEventPriority = (event: TelemetryEvent): number => {
    const priorities: Record<string, number> = {
        campaign: 12,
        strategy: 11,
        doctrine: 10,
        technology: 9,
        combat: 8,
        system: 6,
        movement: 5,
        construction: 4,
        diplomacy: 3,
        economy: 2
    };
    return priorities[event.category] || 0;
};
