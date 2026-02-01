
// --- Additional Analysis Charts ---

// Initialize New Charts
function initAnalysisCharts() {
    // Territory Count Chart
    const ctxTerritory = document.getElementById('territoryCountChart')?.getContext('2d');
    if (ctxTerritory) {
        charts.territoryCount = new Chart(ctxTerritory, {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: true, title: { display: true, text: 'Turn' }, grid: { color: '#334155' } },
                    y: { display: true, beginAtZero: true, title: { display: true, text: 'Planets Controlled' }, grid: { color: '#334155' } }
                },
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: 'Territory Expansion' }
                }
            }
        });
    }

    // Battle Stats Chart
    const ctxBattle = document.getElementById('battleStatsChart')?.getContext('2d');
    if (ctxBattle) {
        charts.battleStats = new Chart(ctxBattle, {
            type: 'bar',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true, display: true, title: { display: true, text: 'Turn' }, grid: { color: '#334155' } },
                    y: { stacked: true, display: true, beginAtZero: true, title: { display: true, text: 'Battles' }, grid: { color: '#334155' } }
                },
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: 'Battle Outcomes (Won/Lost)' }
                }
            }
        });
    }
}

// Call init in main loop (Hook logic will be added via replace, or we just call it if appended)
// We'll hook into initializeCharts by calling this manually if we can't edit it easily,
// but for now let's define the loaders.

async function loadTerritoryData() {
    showChartLoading('territoryCountChart');
    try {
        const factions = globalFilters.selectedFactions.join(',');
        const { min, max } = globalFilters.turnRange;
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&downsample=500`;

        const res = await fetch(`/api/history/territory?${query}`);
        const data = await res.json();
        updateTerritoryChart(data);
    } catch (error) {
        console.error('Failed to load territory data:', error);
    } finally {
        hideChartLoading('territoryCountChart');
    }
}

function updateTerritoryChart(data) {
    const chart = charts.territoryCount;
    if (!chart || !data || !data.factions) return;

    chart.data.datasets = [];
    let allTurns = new Set();

    Object.entries(data.factions).forEach(([faction, history]) => {
        if (!history.turns) return;
        history.turns.forEach(t => allTurns.add(t));

        chart.data.datasets.push({
            label: faction,
            data: history.turns.map((t, i) => ({ x: t, y: history.values[i] })),
            borderColor: getFactionColor(faction),
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.2
        });
    });

    chart.data.labels = Array.from(allTurns).sort((a, b) => a - b);
    chart.update('none');
}

async function loadBattleStatsData() {
    showChartLoading('battleStatsChart');
    try {
        const factions = globalFilters.selectedFactions.join(',');
        const { min, max } = globalFilters.turnRange;
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&downsample=500`;

        const res = await fetch(`/api/history/battle_stats?${query}`);
        const data = await res.json();
        updateBattleStatsChart(data);
    } catch (error) {
        console.error('Failed to load battle stats:', error);
    } finally {
        hideChartLoading('battleStatsChart');
    }
}

function updateBattleStatsChart(data) {
    const chart = charts.battleStats;
    if (!chart || !data || !data.factions) return;

    chart.data.datasets = [];
    let allTurns = new Set();

    // We need to aggregate turns across factions
    // But Bar chart is tricky with multiple factions + stacked wins/losses.
    // Better strategy: If 1 faction selected, show Wins (Green) vs Losses (Red).
    // If multiple: Show Net Wins? Or just total Battles?
    // Let's stick to: Wins (Positive) vs Losses (Negative - manual calc? No, stacked).

    // Simplified: Only show for Primary Selected Faction to avoid clutter
    const primary = globalFilters.selectedFactions[0];
    if (primary && data.factions[primary]) {
        const history = data.factions[primary];

        chart.data.labels = history.turns;

        chart.data.datasets = [
            {
                label: 'Wins',
                data: history.wins,
                backgroundColor: '#22c55e',
                stack: 'Stack 0'
            },
            {
                label: 'Losses',
                data: history.losses,
                backgroundColor: '#ef4444',
                stack: 'Stack 0'
            }
        ];

        chart.options.plugins.title.text = `Battle Outcomes: ${primary}`;
    } else {
        // Multi-faction View? Just show Total Battles?
        // Let's reset if multiple
        chart.data.labels = [];
        chart.data.datasets = [];
        chart.options.plugins.title.text = "Select Single Faction for Detail";
    }

    chart.update('none');
}
