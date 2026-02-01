import React, { useState, useEffect, useRef } from 'react';
import styles from './FactionFilter.module.css';
import { useFiltersStore } from '../../stores/filtersStore';
import { FactionFilterProps } from '../../types/components';

export const FactionFilter: React.FC<FactionFilterProps> = ({ factions }) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const { selectedFactions, toggleFaction, setFactions } = useFiltersStore();

    const toggleDropdown = () => setIsOpen(!isOpen);

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    const handleToggleAll = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (selectedFactions.length === factions.length) {
            // If all selected, and we want to deselect... 
            // User rules say prevent deselecting last faction, 
            // but "Clear All" usually leaves the first one or we can just require 1.
            setFactions([factions[0]]);
        } else {
            setFactions([...factions]);
        }
    };

    const getDisplayText = () => {
        if (selectedFactions.length === 0) return 'None Selected';
        if (selectedFactions.length === factions.length) return 'All Factions';
        if (selectedFactions.length === 1) return selectedFactions[0];
        return `${selectedFactions.length} Factions Selected`;
    };

    return (
        <div className={`${styles.multiSelectContainer} ${isOpen ? styles.open : ''}`} ref={containerRef}>
            <div className={styles.multiSelectDisplay} onClick={toggleDropdown}>
                {getDisplayText()}
            </div>

            <div className={`${styles.multiSelectDropdown} ${isOpen ? styles.show : ''}`}>
                <div
                    className={styles.multiSelectOption}
                    onClick={handleToggleAll}
                    style={{ borderBottom: '1px solid var(--border)', fontWeight: 'bold' }}
                >
                    <input
                        type="checkbox"
                        readOnly
                        checked={selectedFactions.length === factions.length}
                    />
                    {selectedFactions.length === factions.length ? 'Deselect All' : 'Select All'}
                </div>

                {factions.map(faction => (
                    <div
                        key={faction}
                        className={`${styles.multiSelectOption} ${selectedFactions.includes(faction) ? styles.optionSelected : ''}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            // Prevent deselecting last
                            if (selectedFactions.includes(faction) && selectedFactions.length === 1) return;
                            toggleFaction(faction);
                        }}
                    >
                        <input
                            type="checkbox"
                            readOnly
                            checked={selectedFactions.includes(faction)}
                        />
                        {faction}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default FactionFilter;
