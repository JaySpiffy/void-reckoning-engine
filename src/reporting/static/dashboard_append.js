
// --- Fleet Power & Tech Feed Extensions (Appended) ---

async function loadFleetPowerData() {
    showChartLoading('fleetPowerChart');
    try {
        const factions = globalFilters.selectedFactions.join(',');
        const { min, max } = globalFilters.turnRange;
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&downsample=500`;

        const res = await fetch(`/api/military/fleet_history?${query}`);
        const data = await res.json();
        updateFleetPowerChart(data, comparisonModeEnabled ? ghostData.fleetPower : null);
    } catch (error) {
        console.error('Failed to load fleet power data:', error);
    } finally {
        hideChartLoading('fleetPowerChart');
    }
}

function updateFleetPowerChart(data, comparisonData = null) {
    const chart = charts.fleetPower;
    if (!chart || !data || !data.factions) return;

    chart.data.datasets = [];
    let allTurns = new Set();

    // Process Factions
    Object.entries(data.factions).forEach(([faction, history]) => {
        if (!history.turns) return;
        history.turns.forEach(t => allTurns.add(t));

        chart.data.datasets.push({
            label: faction,
            data: history.turns.map((t, i) => ({ x: t, y: history.values[i] })),
            borderColor: getFactionColor(faction),
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0
        });
    });

    chart.data.labels = Array.from(allTurns).sort((a, b) => a - b);
    chart.update('none');
}

function setupTechFeedListener() {
    // Poll for socket availability
    const checkSocket = setInterval(() => {
        if (window.socket || socket) { // Try both global vars
            const s = window.socket || socket;
            clearInterval(checkSocket);
            console.log("Setting up Tech Feed Listener...");

            s.on('tech_unlocked', (event) => {
                updateTechFeed(event);
            });

            // Also listen for general telemetry if tech is embedded
            s.on('telemetry', (event) => {
                if (event.category === 'TECHNOLOGY' || event.data?.tech_id) {
                    updateTechFeed({
                        faction: event.faction,
                        tech_id: event.data?.tech_id || event.tech_id,
                        description: event.message,
                        turn: event.turn,
                        cost: event.data?.cost
                    });
                }
            });
        }
    }, 1000);
}

function updateTechFeed(event) {
    const list = document.getElementById('tech-timeline-list');
    if (!list) return;

    const li = document.createElement('li');
    li.className = 'timeline-item';
    // Style marker based on faction
    const color = getFactionColor(event.faction || 'Unknown');

    // Content
    const time = event.turn ? `Turn ${event.turn}` : 'Now';
    const techName = event.tech_id || 'Unknown Tech';
    const cost = event.cost ? `(${event.cost} Req)` : '';

    li.innerHTML = `
        <div class="timeline-marker" style="background-color: ${color};"></div>
        <div class="timeline-content">
            <div class="timeline-header">
                <span class="timeline-title">${techName}</span>
                <span class="timeline-time">${time}</span>
            </div>
            <div class="timeline-desc">${event.faction} unlocked ${techName} ${cost}</div>
        </div>
    `;

    list.insertBefore(li, list.firstChild);
    if (list.children.length > 20) list.removeChild(list.lastChild);
}
