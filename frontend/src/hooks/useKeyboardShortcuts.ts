import { useEffect } from 'react';

interface KeyboardShortcutOptions {
    onExport: () => void;
    onBookmarks: () => void;
}

export const useKeyboardShortcuts = ({ onExport, onBookmarks }: KeyboardShortcutOptions) => {
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Check for Ctrl/Cmd + key
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'e':
                        e.preventDefault();
                        onExport();
                        break;
                    case 'b':
                        e.preventDefault();
                        onBookmarks();
                        break;
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onExport, onBookmarks]);
};
