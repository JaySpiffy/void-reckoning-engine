export const notifications = {
    success: (message: string) => {
        // Since we don't have a toast library yet, we use a simple alert or console
        // In a real app, this would trigger a Toast component
        console.log('SUCCESS:', message);
    },
    error: (message: string) => {
        console.error('ERROR:', message);
        alert(`CRITICAL ERROR: ${message}`);
    },
    info: (message: string) => {
        console.log('INFO:', message);
    }
};

export default notifications;
