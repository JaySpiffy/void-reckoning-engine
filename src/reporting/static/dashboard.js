// Global State
let socket = null;
let charts = {};
const MAX_DATA_POINTS = 50;

let galaxyMap = {
    canvas: null,
    ctx: null,
    systems: [],
    lanes: [],
    transform: { x: 0, y: 0, scale: 1 },
    isDragging: false,
    lastMouse: { x: 0, y: 0 },
    animations: [],
    galaxyRatio: 1,
    galaxyBounds: null
};

let isHistoricalMode = false;
let currentHistoricalTurn = 1;

// Faction Colors
const FACTION_COLORS = {
    "Hegemony": "#FFD700", // Gold
    "Chaos": "#8B0000",    // Dark Red
    "Aether-Kin": "#4169E1",    // Royal Blue
    "Marauders": "#228B22",     // Forest Green
    "Tau": "#00CED1",      // Dark Turquoise
    "Hierarchs": "#32CD32",  // Lime Green
    "Bio-Morphs": "#8B008B", // Dark Magenta
    "Unknown": "#808080"
};

let comparisonModeEnabled = false;
let ghostData = {};
let currentUniverse = 'unknown'; // Will be set by status
let currentRunId = 'unknown';
let currentBatchId = 'unknown';

// Global Filters State (Step 1)
let globalFilters = {
    selectedFactions: [],
    turnRange: { min: 1, max: 1 },
    visibleMetrics: {
        netProfit: true,
        revenueBreakdown: true,
        stockpileVelocity: true,
        resourceRoi: true,
        combatEffectiveness: true,
        forceComposition: true,
        attritionRate: true,
        battleHeatmap: true,
        industrialDensity: true,
        queueEfficiency: true,
        techTreeProgress: true,
        researchRoi: true
    },
    comparisonMode: false
};

// --- Debugging & Diagnostics (Step 3) ---
window.DASHBOARD_DEBUG = localStorage.getItem('dashboard_debug') === 'true' ||
    new URLSearchParams(window.location.search).get('debug') === 'true';

const debugHistory = [];
const MAX_DEBUG_HISTORY = 200;

// --- Utility Functions ---

const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
};

function debugLog(category, message, data = null) {
    if (!window.DASHBOARD_DEBUG && category !== 'ERROR') return;

    const entry = {
        timestamp: new Date().toISOString(),
        category,
        message,
        data
    };

    debugHistory.unshift(entry);
    if (debugHistory.length > MAX_DEBUG_HISTORY) debugHistory.pop();

    const prefix = `[${category}]`;
    const styles = {
        'SOCKET': 'color: #0ea5e9; font-weight: bold;',
        'API': 'color: #10b981; font-weight: bold;',
        'RENDER': 'color: #a855f7; font-weight: bold;',
        'ERROR': 'color: #ef4444; font-weight: bold;'
    }[category] || 'font-weight: bold;';

    if (data) {
        console.log(`%c${prefix} ${message}`, styles, data);
    } else {
        console.log(`%c${prefix} ${message}`, styles);
    }
}

// Expose debug tools
window.toggleDebug = () => {
    window.DASHBOARD_DEBUG = !window.DASHBOARD_DEBUG;
    localStorage.setItem('dashboard_debug', window.DASHBOARD_DEBUG);
    console.log(`Debug Mode: ${window.DASHBOARD_DEBUG ? 'ON' : 'OFF'}`);
};

window.exportDebugLogs = () => {
    const blob = new Blob([JSON.stringify(debugHistory, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-logs-${Date.now()}.json`;
    a.click();
};

function showUserError(title, details = null) {
    const container = document.getElementById('global-error-container');
    if (!container) {
        console.error("Global Error Container missing!", title, details);
        return;
    }

    // Prevent duplicates
    const existing = Array.from(container.children).find(c => c.innerHTML.includes(title));
    if (existing) return;

    const errorId = 'err-' + Date.now();
    const html = `
        <div id="${errorId}" class="error-banner" style="background: rgba(239, 68, 68, 0.2); border-left: 4px solid #ef4444; padding: 1rem; margin-bottom: 0.5rem; color: #fff; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="font-weight: bold; margin: 0; font-size: 1rem;">⚠️ ${title}</h3>
                    ${details ? `<p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">${details}</p>` : ''}
                </div>
                <button onclick="document.getElementById('${errorId}').remove()" style="background: none; border: none; color: #fff; cursor: pointer; font-size: 1.2rem;">&times;</button>
            </div>
        </div>
    `;

    container.innerHTML += html;
    container.classList.remove('hidden');
}

function logDashboardError(context, error, details = {}) {
    debugLog('ERROR', `${context}: ${error.message || error}`, details);
    if (window.DASHBOARD_DEBUG) console.error(error);
}

// --- API Wrappers ---
async function fetchWithLogging(url, options = {}) {
    const start = performance.now();
    try {
        debugLog('API', `REQ: ${url}`);
        const response = await fetch(url, options);
        const duration = performance.now() - start;

        debugLog('API', `RES: ${url} [${response.status}] ${duration.toFixed(1)}ms`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response;
    } catch (error) {
        logDashboardError('API Fetch', error, { url });
        throw error;
    }
}

// Performance & Pagination State (Step 8-12)
let performanceStats = {
    history: { memory: [], cache: [] },
    profiling: false
};

class PaginationManager {
    constructor(id, pageSize = 20) {
        this.id = id;
        this.pageSize = pageSize;
        this.currentPage = 1;
        this.total = 0;
    }
    update(total) {
        this.total = total;
        this.render();
    }
    render() {
        const container = document.getElementById(`${this.id}-pagination`);
        if (!container) return;
        const totalPages = Math.ceil(this.total / this.pageSize) || 1;
        container.innerHTML = `
            <div class="pagination-controls">
                <button class="btn-page" ${this.currentPage <= 1 ? 'disabled' : ''} onclick="handlePageChange('${this.id}', ${this.currentPage - 1})">PREV</button>
                <span class="page-info">PAGE ${this.currentPage} / ${totalPages} (${this.total} TOTAL)</span>
                <button class="btn-page" ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="handlePageChange('${this.id}', ${this.currentPage + 1})">NEXT</button>
            </div>
        `;
    }
}

const pagination = {
    telemetry: new PaginationManager('telemetry'),
    alerts: new PaginationManager('alerts')
};

// Lazy Loading Observer (Step 9)
// --- Lazy Loading & Resize Observations ---
const chartObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const chartId = entry.target.dataset.chartId;
            if (chartId) { // Validate ID
                console.log(`[LazyLoad] Loading data for ${chartId}`);
                // Special mapping for plural discrepancies if needed, but loaders keys usually match data-chart-id
                loadChartDataLazily(chartId).catch(err => {
                    logDashboardError('LazyLoad', err, { chartId });
                    showChartError(`${chartId}Chart`, 'Failed to load');
                });
                chartObserver.unobserve(entry.target);
            }
        }
    });
}, { threshold: 0.1 });

const chartResizeObserver = new ResizeObserver(entries => {
    entries.forEach(entry => {
        const chartId = entry.target.dataset.chartId;
        // Map data-chart-id to chart instance key
        if (chartId && charts[chartId]) {
            charts[chartId].resize();
        }
    });
});


function toggleComparisonMode(enabled) {
    comparisonModeEnabled = enabled;
    localStorage.setItem('comparison_mode', enabled);


    if (enabled) {
        // Fetch baseline economic data for charts
        // Need to identify baseline run_id first. 
        // We can fetch the comparison summary first to get the baseline ID, OR just fetch "gold_standard" reports directly.
        // The endpoints support ?run_id=...
        // Let's assume we need to get the baseline ID from the comparison endpoint, THEN fetch the timeseries.

        // 1. Get Comparison Summary to find baseline IDs
        fetchWithLogging('/api/reports/compare/runs/gold_standard?universe=' + currentUniverse + '&run_id=' + currentRunId + '&batch_id=' + currentBatchId)
            .then(r => r.json())
            .then(compData => {
                const baselineRunId = compData.baseline?.run_id;
                const baselineBatchId = compData.baseline?.batch_id;

                if (!baselineRunId) throw new Error("No baseline run found");

                // 2. Fetch Time Series for Baseline
                const p1 = fetchWithLogging(`/api/economic/net_profit?universe=${currentUniverse}&run_id=${baselineRunId}&batch_id=${baselineBatchId}&faction=all`).then(r => r.json());
                const p2 = fetchWithLogging(`/api/economic/stockpile_velocity?universe=${currentUniverse}&run_id=${baselineRunId}&batch_id=${baselineBatchId}&faction=all`).then(r => r.json());

                // Military Baselines
                const p3 = fetchWithLogging(`/api/military/combat_effectiveness?universe=${currentUniverse}&run_id=${baselineRunId}&batch_id=${baselineBatchId}&faction=all`).then(r => r.json());
                const p4 = fetchWithLogging(`/api/military/attrition_rate?universe=${currentUniverse}&run_id=${baselineRunId}&batch_id=${baselineBatchId}&faction=all`).then(r => r.json());

                return Promise.all([p1, p2, p3, p4]);
            })
            .then(([netProfit, velocity, cer, attrition]) => {
                ghostData = {
                    net_profit: netProfit,
                    velocity: velocity,
                    cer: cer,
                    attrition: attrition
                };
                refreshEconomicCharts();
                refreshAllCharts(); // Refresh everything to show ghost data
            })
            .catch(err => {
                console.error('Failed to load comparison data:', err);
                comparisonModeEnabled = false;
                const toggle = document.getElementById('comparison-mode-toggle');
                if (toggle) toggle.checked = false;
            });
    } else {
        ghostData = {};
        refreshEconomicCharts();
    }
}

function refreshEconomicCharts() {
    loadEconomicData();
}

// --- Chart Validation ---
function validateChartSetup() {
    const requiredCharts = [
        'resources', 'production', 'netProfit', 'revenueBreakdown',
        'stockpileVelocity', 'resourceRoi', 'combatEffectiveness',
        'forceComposition', 'attritionRate', 'battleHeatmap',
        'industrialDensity', 'queueEfficiency', 'techTreeProgress',
        'anomalySeverity', 'fleetPower', 'territoryCount', 'battleStats'
    ];

    const missing = [];
    requiredCharts.forEach(chartId => {
        const container = document.querySelector(`[data-chart-id="${chartId}"]`);
        // Handle both ID naming conventions: IDChart or just IDCanvas (common pattern variation)
        const canvas = document.getElementById(`${chartId}Chart`) || document.getElementById(`${chartId}Canvas`) || document.getElementById(chartId + 'Canvas');

        if (!container) missing.push(`Container for ${chartId}`);
        if (!canvas) {
            // Special case for heatmap which might be a div or canvas
            if (chartId !== 'battleHeatmap' || !document.getElementById('battleHeatmapCanvas')) {
                missing.push(`Canvas for ${chartId}`);
            }
        }
    });

    if (missing.length > 0) {
        console.warn('Missing chart elements:', missing);
        // Add visual warning?
    }

    return missing.length === 0;
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    validateChartSetup(); // Add validation here

    // Attach Observers
    document.querySelectorAll('.chart-container[data-chart-id]').forEach(container => {
        chartObserver.observe(container);
        chartResizeObserver.observe(container);
    });

    initAnalysisCharts(); // New Hook
    initGalaxyMap(); // New Map
    loadInitialData();
    connectWebSocket();
    setupTechFeedListener(); // New Listener
    startControlPolling(); // New Polling
    initRunSelector(); // New Run Selector
});

// --- Run Selector Logic ---
async function initRunSelector() {
    try {
        // Fetch universe from global or wait for status
        // We might not know universe yet if status failed. 
        // But usually we default to 'void_reckoning'.

        // Wait for universe to be set? 
        // Or just fetch runs without universe filter first (API supports it?)
        // The API defaults to None, which might return all. 
        // Let's rely on dashboard service current status.

        const response = await fetchWithLogging('/api/runs?universe=' + currentUniverse);
        const runs = await response.json();

        const selector = document.getElementById('run-selector');
        if (!selector) return;

        // Clear existing options (keep placeholder)
        selector.innerHTML = '<option value="" disabled>Select Run...</option>';

        runs.forEach(run => {
            const date = new Date(run.started_at * 1000).toLocaleString();
            const option = document.createElement('option');
            option.value = run.run_id;
            // Mark active run
            if (run.run_id === currentRunId) {
                option.selected = true;
            }

            // Format: "RunID (Date) [Turns: N]"
            option.text = `${run.run_id} (${date}) [T:${run.turns_taken}]`;
            selector.appendChild(option);
        });

    } catch (e) {
        console.error("Failed to init run selector:", e);
    }
}

window.handleRunSwitch = async function (runId) {
    if (!runId || runId === currentRunId) return;

    if (!confirm(`Switch to run ${runId}? Current view will be reset.`)) {
        // Revert selection
        const selector = document.getElementById('run-selector');
        selector.value = currentRunId || "";
        return;
    }

    try {
        showUserError("Switching Simulation Context...", "Please wait while dashboard resets.");

        await fetchWithLogging('/api/control/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ run_id: runId })
        });

        // Hard reload to clear all frontend state (charts, caches, sockets)
        window.location.reload();

    } catch (e) {
        showUserError("Switch Failed", e.message);
    }
};

// --- Filter & Multi-select Logic ---

function toggleMultiSelect(el) {
    const dropdown = el.querySelector('.multi-select-dropdown');
    if (!dropdown) return;

    // Close other dropdowns
    document.querySelectorAll('.multi-select-dropdown.show').forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });

    dropdown.classList.toggle('show');

    // Close when clicking outside
    const outsideClickListener = (event) => {
        if (!el.contains(event.target)) {
            dropdown.classList.remove('show');
            document.removeEventListener('click', outsideClickListener);
        }
    };

    if (dropdown.classList.contains('show')) {
        document.addEventListener('click', outsideClickListener);
    }
}

function updateMultiSelectDisplay(id, selectedCount, totalCount) {
    const el = document.getElementById(id);
    if (!el) return;
    const display = el.querySelector('.multi-select-display');
    if (!display) return;

    if (selectedCount === 0) {
        display.innerText = "None Selected";
    } else if (selectedCount === totalCount) {
        display.innerText = "All Factions";
    } else {
        display.innerText = `${selectedCount} Factions`;
    }
}

const refreshChartDebounce = debounce(() => {
    refreshAllCharts();
}, 500);

function handleFactionToggle(faction, checked) {
    if (checked) {
        if (!globalFilters.selectedFactions.includes(faction)) {
            globalFilters.selectedFactions.push(faction);
        }
    } else {
        if (globalFilters.selectedFactions.length > 1) {
            globalFilters.selectedFactions = globalFilters.selectedFactions.filter(f => f !== faction);
        } else {
            // Prevent deselecting the last faction? Or allow it implies "all" or "none"?
            // Let's enforce at least one, or fallback to 'all' logic if handled
            console.warn("Cannot deselect last faction");
            // Re-check the box visually
            setTimeout(() => syncFactionFilters(), 50);
            return;
        }
    }
    syncFactionFilters();
    refreshChartDebounce();
}

function syncFactionFilters() {
    // Update all dropdown checkboxes to match global state
    document.querySelectorAll('.multi-select-dropdown input[type="checkbox"]').forEach(cb => {
        cb.checked = globalFilters.selectedFactions.includes(cb.value);
    });

    const dropdowns = ['global-faction-filter', 'economic-faction-filter-multi', 'military-faction-filter-multi', 'development-faction-filter-multi'];
    dropdowns.forEach(id => {
        const total = document.querySelectorAll(`#${id.replace('-multi', '').replace('global-', 'global-')} .multi-select-option`).length || 8; // fallback
        updateMultiSelectDisplay(id, globalFilters.selectedFactions.length, total);
    });
}

function initFilterControls() {
    // Populate metric toggles
    const panel = document.getElementById('metric-visibility-toggles');
    if (panel) {
        panel.innerHTML = Object.keys(globalFilters.visibleMetrics).map(m => `
            <div class="toggle-item">
                <input type="checkbox" id="toggle-${m}" ${globalFilters.visibleMetrics[m] ? 'checked' : ''} onchange="toggleMetricVisibility('${m}', this.checked)">
                <label for="toggle-${m}">${m.replace(/([A-Z])/g, ' $1')}</label>
            </div>
        `).join('');
    }

    // Turn slider max turn fetch
    fetchWithLogging('/api/run/max_turn?universe=' + currentUniverse + '&run_id=' + currentRunId)
        .then(r => r.json())
        .then(data => {
            const max = data.max_turn || 1;
            const slider = document.getElementById('turn-range-slider');
            const maxInput = document.getElementById('turn-range-max');
            if (slider) {
                slider.max = max;
                slider.value = max;
            }
            if (maxInput) maxInput.value = max;
            globalFilters.turnRange.max = max;
        });
}

function handleRangeSliderChange(val) {
    globalFilters.turnRange.max = parseInt(val);
    document.getElementById('turn-range-max').value = val;
    // Single slider usually controls "Max" or "Current View"? 
    // If it's a range slider, it usually has two knobs. 
    // Assuming this slider controls the "Max" of the range, effectively sliding the window end.
    // Or if it's a "Look at Turn X" slider.
    // Based on existing code `min, max`, let's assume this slider updates the MAX, and keeps the window size?
    // OR updates the current turn focus.

    // Let's implement it as updating the MAX turn, extending range from 1 to VAL
    const max = parseInt(val);
    document.getElementById('turn-range-max').value = max;
    syncTurnInputs();
}

function syncTurnInputs() {
    let min = parseInt(document.getElementById('turn-range-min').value) || 1;
    let max = parseInt(document.getElementById('turn-range-max').value) || 1;
    const maxPossible = parseInt(document.getElementById('turn-range-slider').max) || 100;

    // Validate
    if (min < 1) min = 1;
    if (max > maxPossible) max = maxPossible;
    if (min > max) min = max; // Enforce Order

    globalFilters.turnRange = { min, max };

    // Update UI (to reflect corrections)
    document.getElementById('turn-range-min').value = min;
    document.getElementById('turn-range-max').value = max;

    refreshChartDebounce();
}

function toggleMetricVisibility(metric, visible) {
    globalFilters.visibleMetrics[metric] = visible;

    // Select chart container
    // We need to map metric keys to DOM IDs
    const idMap = {
        netProfit: 'netProfitChart',
        revenueBreakdown: 'revenueBreakdownChart',
        stockpileVelocity: 'stockpileVelocityChart',
        resourceRoi: 'resourceRoiChart',
        combatEffectiveness: 'combatEffectivenessChart',
        forceComposition: 'forceCompositionChart',
        attritionRate: 'attritionRateChart',
        battleHeatmap: 'battleHeatmapCanvas',
        industrialDensity: 'industrialDensityChart',
        queueEfficiency: 'queueEfficiencyChart',
        techTreeProgress: 'techTreeProgressChart',
        researchRoi: 'researchRoiContainer'
    };

    const canvasId = idMap[metric];
    if (canvasId) {
        const container = document.getElementById(canvasId).parentElement;
        if (visible) {
            container.style.display = 'block';
            refreshAllCharts(); // Reload data for the newly shown chart
        } else {
            container.style.display = 'none';
        }
    }

    saveFilterState();
}

// --- Galaxy Map State ---
// --- HEALTH MONITORING ---
function startHealthMonitor() {
    if (window.healthMonitorInterval) clearInterval(window.healthMonitorInterval);

    window.healthMonitorInterval = setInterval(() => {
        if (!socket.connected) return;

        const start = Date.now();
        socket.emit('ping_check', {}, () => {
            const latency = Date.now() - start;
            // Update latency metric if we had a UI element for it
            if (latency > 2000) {
                console.warn(`High latency detected: ${latency}ms`);
            }
        });

        // Stale Connection Check
        // If needed, check last message timestamp
    }, 30000);
}

// Ensure global scope
window.startHealthMonitor = startHealthMonitor;

// Galaxy Map State (Managed globally at top)

function connectWebSocket() {
    // --- WEBSOCKET CONNECTION SETUP ---
    debugLog('SOCKET', 'Initializing WebSocket connection...');

    const socketOptions = {
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000
    };

    // Connection State Tracking
    let connectionState = {
        attempts: 0,
        lastConnected: null,
        lastDisconnected: null,
        retryCount: 0
    };

    socket = io(socketOptions); // Connects to same host/port

    socket.on('connect', () => {
        const now = Date.now();
        debugLog('SOCKET', 'Connected!', { id: socket.id });

        // Recovery Procedure (Step 9 / Comment 5)
        // If we were disconnected for more than 5 seconds, refresh data
        if (connectionState.lastDisconnected && (now - connectionState.lastDisconnected > 5000)) {
            debugLog('SOCKET', 'Extended disconnect detected. Refreshing snapshot...');
            requestSnapshot();
        }

        connectionState.retryCount = 0;
        connectionState.lastConnected = now;
        connectionState.lastDisconnected = null; // Clear disconnect timestamp

        const el = document.getElementById('connection-status');
        if (el) {
            el.className = 'status-badge online';
            el.innerText = 'ONLINE';
        }

        // Start Health Monitoring if defined (Step 5)
        if (window.startHealthMonitor) window.startHealthMonitor();
    });

    socket.on('disconnect', (reason) => {
        debugLog('SOCKET', `Disconnected: ${reason}`);
        connectionState.lastDisconnected = Date.now();

        const el = document.getElementById('connection-status');
        if (el) {
            el.className = 'status-badge offline';
            el.innerText = 'OFFLINE';
        }
    });

    socket.on('connect_error', (error) => {
        connectionState.retryCount++;
        // connectionState.lastDisconnected = Date.now(); // handled in disconnect usually, but connect_error implies failed attempt

        const backoff = Math.min(1000 * Math.pow(2, connectionState.retryCount), 30000);

        debugLog('SOCKET', `Connection Error (Attempt ${connectionState.retryCount})`, { error: error.message, backoff });

        const el = document.getElementById('connection-status');
        if (el) {
            el.className = 'status-badge offline';
            el.innerText = `RETRY ${connectionState.retryCount}`;
        }
    });

    socket.on('error', (error) => {
        debugLog('ERROR', 'Socket error', error);
    });

    // Debug Mode (Step 8)
    socket.onAny((event, ...args) => {
        // Filter out high-frequency ping/status if needed, but useful for now
        debugLog('SOCKET', `INCOMING: ${event}`, { size: JSON.stringify(args).length });
    });

    socket.on('status_update', (data) => {
        updateMetadata(data);
    });

    socket.on('metrics_update', (metrics) => {
        updateLiveMetrics(metrics);
    });

    // Event Handlers
    socket.on('resource_update', (event) => {
        updateResourceChart(event);
    });

    socket.on('battle_performance_update', (data) => {
        if (!data) return;

        // 1. Update Combat Effectiveness (Bar Chart)
        if (data.faction && data.cer !== undefined && charts.combatEffectiveness) {
            const chart = charts.combatEffectiveness;
            const idx = chart.data.labels.indexOf(data.faction);

            if (idx >= 0) {
                // Update existing bar
                // Determine weighting? If CER is average, we might need running average logic.
                // But for simplicity/MVP, let's just update to latest or push?
                // The backend 'get_faction_combat_effectiveness' returns average over time?
                // Wait, the API returns timeseries or average. The chart shows Average.
                // If we receive a new battle CER, we should update the average.
                // Storing count in dataset? No.
                // Simplification: Just set to new value or ignore to avoid jumpiness.
                // BETTER: Just call loadMilitaryData() to re-fetch accurate aggregates.
                // Comment 3 instructions say: "Refresh charts without full reload"
                // "Append/update latest CER... e.g. push data.cer" (implies timeseries?)
                // But chart is BAR chart of Factions. 
                // So "Append" means update the bar value.
                // We will update the bar value to the NEW snapshot CER?
                // Or we can just re-fetch.
                // Let's implement direct update for responsiveness.
                chart.data.datasets[0].data[idx] = data.cer;
            } else {
                // Add new faction bar
                chart.data.labels.push(data.faction);
                chart.data.datasets[0].data.push(data.cer);
                if (Array.isArray(chart.data.datasets[0].backgroundColor)) {
                    chart.data.datasets[0].backgroundColor.push(getCERColor(data.cer));
                }
            }
            chart.update('none');
        }

        // 2. Update Force Composition (Radar)
        if (data.faction && data.force_composition && charts.forceComposition) {
            const filter = document.getElementById('military-faction-filter');
            if (filter && filter.value === data.faction) {
                updateForceCompositionChart(data.force_composition, data.faction);
            }
        }

        // 3. Update Attrition Rate (Line)
        if (data.faction && data.attrition_rate !== undefined && charts.attritionRate) {
            // We need to add a point {x: turn, y: rate}
            // Data payload now has 'turn'.
            const turn = data.turn || (charts.attritionRate.data.labels[charts.attritionRate.data.labels.length - 1] || 0) + 1;

            const dataset = charts.attritionRate.data.datasets.find(ds => ds.label === data.faction);
            if (dataset) {
                dataset.data.push({ x: turn, y: data.attrition_rate });
                // Sort/Labels update?
                if (!charts.attritionRate.data.labels.includes(turn)) {
                    charts.attritionRate.data.labels.push(turn);
                    charts.attritionRate.data.labels.sort((a, b) => a - b);
                }
                charts.attritionRate.update('none');
            }
        }
    });


    socket.on('heatmap_event', (event) => {
        updateHeatmap(event);
    });

    socket.on('tech_event', (event) => {
        updateTechTimeline(event);
        logEvent(event);
    });

    socket.on('map_update', (event) => {
        if (!event || !event.data || !event.data.planets) return;
        updateMapWithPlanets(event.data.planets);
    });



    // Debounced Loaders
    const debouncedLoadEconomicData = debounce(() => loadEconomicData(), 2000);
    const debouncedLoadIndustrialData = debounce((filter) => loadIndustrialData(filter), 2000);
    const debouncedLoadResearchData = debounce((filter) => loadResearchData(filter), 2000);

    socket.on('economic_update', (data) => {
        // Real-time economic health update
        if (data.net_profit) {
            debouncedLoadEconomicData();
        }
    });

    socket.on('industrial_update', (data) => {
        // Refresh industrial density chart for affected faction
        const filter = document.getElementById('development-faction-filter')?.value || 'all';
        if (filter === 'all' || filter === data.event.faction) {
            updateIndustrialDensityChart(data.density, null, data.event.faction);
            updateQueueEfficiencyChart(data.efficiency);
        }
        // Add to timeline
        debouncedLoadIndustrialData(filter);
    });

    socket.on('research_update', (data) => {
        // Refresh tech tree progress chart for affected faction
        const filter = document.getElementById('development-faction-filter')?.value || 'all';
        if (filter === 'all' || filter === data.event.faction) {
            updateTechTreeProgressChart(data.progress, null, data.event.faction);
        }

        // Add milestone and reload ROI
        debouncedLoadResearchData(filter);
    });

    socket.on('alert_triggered', (alert) => {
        console.log("New Alert Triggered:", alert);
        loadAlertData(); // Refresh list and chart

        // Visual notification
        const msg = document.getElementById('status-message');
        if (msg) {
            msg.innerText = `[ALERT] ${alert.message} `;
            msg.className = `status - badge ${alert.severity === 'critical' ? 'offline' : 'online'} `;
            msg.classList.remove('hidden');
            setTimeout(() => msg.classList.add('hidden'), 5000);
        }
    });
}

function updateMetadata(data) {
    if (data.universe) {
        document.getElementById('universe-name').innerText = data.universe;
        currentUniverse = data.universe;
    }
    if (data.run_id) {
        document.getElementById('run-id').innerText = data.run_id;
        currentRunId = data.run_id;
    }
    if (data.live_metrics) updateLiveMetrics(data.live_metrics);
    if (data.paused !== undefined) {
        isPaused = data.paused;
        updateControlUI();
    }
}



async function loadEconomicData() {
    showChartLoading('netProfitChart');
    try {
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}`;
        const factions = globalFilters.selectedFactions.join(',');
        const [histRes, velRes] = await Promise.all([
            fetchWithLogging(`/api/economic/net_profit?${query}&faction=${factions}`),
            fetchWithLogging(`/api/economic/stockpile_velocity?${query}&faction=${factions}`)
        ]);
        const histData = await histRes.json();
        const velData = await velRes.json();
        updateNetProfitChart(histData, comparisonModeEnabled ? ghostData.netProfit : null);
        updateStockpileVelocityChart(velData, comparisonModeEnabled ? ghostData.stockpile : null);
    } catch (e) { console.error("Failed loadEconomicData", e); }
    finally { hideChartLoading('netProfitChart'); }
}

async function loadMilitaryData() {
    showChartLoading('combatEffectivenessChart');
    try {
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}`;
        const factions = globalFilters.selectedFactions.join(',');
        const [cerRes, compRes, attRes] = await Promise.all([
            fetchWithLogging(`/api/military/combat_effectiveness?${query}&faction=${factions}`),
            fetchWithLogging(`/api/military/force_composition?${query}&faction=${factions}`),
            fetchWithLogging(`/api/military/attrition_rate?${query}&faction=${factions}`)
        ]);
        updateCombatEffectivenessChart(await cerRes.json());
        updateForceCompositionChart(await compRes.json(), factions[0] || 'all');
        updateAttritionRateChart(await attRes.json());
    } catch (e) {
        console.error("Failed to load military details:", e);
    } finally {
        hideChartLoading('combatEffectivenessChart');
    }
}

async function loadInitialData() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('hidden');

    try {
        const [statusRes, factionsRes] = await Promise.all([
            fetchWithLogging('/api/status'),
            fetchWithLogging('/api/galaxy/factions')
        ]);

        const status = await statusRes.json();
        const factions = await factionsRes.json();

        if (status.universe) {
            updateMetadata(status);
            currentUniverse = status.universe;
        }
        if (status.run_id) currentRunId = status.run_id;
        if (status.batch_id) currentBatchId = status.batch_id;

        if (status.paused !== undefined) {
            isPaused = status.paused;
            updateControlUI();
        }

        // Initialize Filter Controls
        initFilterControls();

        // Populate Multi-select Faction Filters
        if (factions && Array.isArray(factions)) {
            // Helper to populate if function exists, else skip
            if (typeof populateFactionMultiSelect === 'function') {
                populateFactionMultiSelect('global-faction-dropdown', factions, 'global');
                populateFactionMultiSelect('economic-faction-dropdown', factions, 'global');
                populateFactionMultiSelect('military-faction-dropdown', factions, 'global');
                populateFactionMultiSelect('development-faction-dropdown', factions, 'global');
            }

            // Set default selected factions
            globalFilters.selectedFactions = [...factions];
            syncFactionFilters();
        }

        // Load Alert Data initially
        await loadAlertData();

        // Initialize Lazy Loading (Step 9)
        document.querySelectorAll('.chart-container').forEach(c => chartObserver.observe(c));

        // Load initial telemetry
        await loadTelemetryData();

        // Restore comparison mode from localStorage
        const savedComparisonMode = localStorage.getItem('comparison_mode') === 'true';
        if (savedComparisonMode) {
            const toggle = document.getElementById('comparison-mode-toggle');
            if (toggle) {
                toggle.checked = true;
                toggleComparisonMode(true);
            }
        }
    } catch (error) {
        console.error('Failed to load initial data:', error);
        showUserError("Failed to load dashboard configuration", "Check server connection");
    } finally {
        if (overlay) overlay.classList.add('hidden');
    }
}

function populateFactionMultiSelect(containerId, factions, category) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = factions.map(f => `
        <div class="multi-select-option" onclick="event.stopPropagation()">
            <input type="checkbox" id="cb-${containerId}-${f}" data-faction="${f}" onchange="handleFactionToggle('${f}', this.checked, '${category}')" checked>
            <label for="cb-${containerId}-${f}">${f}</label>
        </div>
    `).join('');

    // Add Select All / Deselect All buttons
    const footer = document.createElement('div');
    footer.className = 'flex justify-between p-2 border-t border-border mt-1';
    footer.style.display = 'flex';
    footer.style.justifyContent = 'space-between';
    footer.style.padding = '0.5rem';
    footer.style.borderTop = '1px solid var(--border)';

    footer.innerHTML = `
        <button class="btn-outline" style="font-size: 0.65rem; padding: 2px 5px;" onclick="setAllFactions(true, '${containerId}', '${category}')">All</button>
        <button class="btn-outline" style="font-size: 0.65rem; padding: 2px 5px;" onclick="setAllFactions(false, '${containerId}', '${category}')">None</button>
    `;
    container.appendChild(footer);
}

function setAllFactions(active, containerId, category) {
    const container = document.getElementById(containerId);
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = active;
        const faction = cb.getAttribute('data-faction');
        if (category === 'global') {
            if (active) {
                if (!globalFilters.selectedFactions.includes(faction)) globalFilters.selectedFactions.push(faction);
            } else {
                globalFilters.selectedFactions = globalFilters.selectedFactions.filter(f => f !== faction);
            }
        }
    });

    if (category === 'global') {
        syncFactionFilters();
        refreshAllCharts();
    }
    saveFilterState();
}

function showChartLoading(chartId) {
    const base = chartId.replace('Chart', '');
    const skeleton = document.getElementById(`skeleton-${base}`);
    const canvas = document.getElementById(chartId);
    if (skeleton) skeleton.classList.remove('hidden');
    if (canvas) canvas.classList.add('hidden');
}

function hideChartLoading(chartId) {
    const base = chartId.replace('Chart', '');
    const skeleton = document.getElementById(`skeleton-${base}`);
    const canvas = document.getElementById(chartId);
    if (skeleton) skeleton.classList.add('hidden');
    if (canvas) canvas.classList.remove('hidden');
}

async function loadResearchData() {
    showChartLoading('techTreeProgressChart');
    try {
        const factions = globalFilters.selectedFactions.join(',');
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}`;

        const progressRes = await fetchWithLogging(`/api/research/tech_tree_progress?${query}`);
        const progressData = await progressRes.json();
        updateTechTreeProgressChart(progressData, comparisonModeEnabled ? ghostData.techProgress : null);

        const primaryFaction = globalFilters.selectedFactions[0] || 'all';
        if (primaryFaction !== 'all') {
            const roiRes = await fetchWithLogging(`/api/research/roi?${query}&faction=${primaryFaction}`);
            const roiData = await roiRes.json();
            updateResearchRoiCards(roiData);
        }

        const timelineRes = await fetchWithLogging(`/api/research/timeline?universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&limit=20`);
        const timelineData = await timelineRes.json();
        updateResearchTimeline(timelineData);
    } catch (e) {
        console.error("Failed to load research data:", e);
    } finally {
        hideChartLoading('techTreeProgressChart');
    }
}


async function loadIndustrialData(filter = 'all') {
    showChartLoading('industrialDensityChart');
    try {
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}`;
        const finalUrl = `/api/industrial/density?${query}&faction=${filter === 'all' ? globalFilters.selectedFactions.join(',') : filter}`;

        const res = await fetchWithLogging(finalUrl);
        const data = await res.json();

        updateIndustrialDensityChart(data, comparisonModeEnabled ? ghostData.industrial : null, filter !== 'all' ? filter : null);

        if (data.efficiency !== undefined) {
            updateQueueEfficiencyChart(data);
        }
    } catch (e) {
        console.error("Failed to load industrial data:", e);
    } finally {
        hideChartLoading('industrialDensityChart');
    }
}

function loadDevelopmentPulseData() {
    loadIndustrialData();
    loadResearchData();
}

function populateResourceHistory(faction, history) {
    if (!history || !history.turns || !history.values) return;

    const chart = charts.resources;
    if (!chart) return;

    let dataset = chart.data.datasets.find(ds => ds.label === faction);
    if (!dataset) {
        dataset = {
            label: faction,
            borderColor: getFactionColor(faction),
            data: [],
            fill: false,
            tension: 0.4
        };
        chart.data.datasets.push(dataset);
    }

    dataset.data = history.values.slice(-MAX_DATA_POINTS);
    chart.data.labels = history.turns.slice(-MAX_DATA_POINTS); // Sync labels
    chart.update();
}

function populateBattleHeatmap(battles) {
    // Deprecated for Galaxy Map
}

async function initGalaxyMap() {
    const canvas = document.getElementById('galaxyMap');
    if (!canvas) return;

    galaxyMap.canvas = canvas;
    galaxyMap.ctx = canvas.getContext('2d');

    // Resize Listener
    // Resize Listener
    const resizeInfo = () => {
        const dpr = window.devicePixelRatio || 1;
        const parentRect = canvas.parentElement.getBoundingClientRect();
        const width = parentRect.width;
        let height = 600; // Default fallback

        // If we have galaxy aspect ratio, use it to calculate optimal height
        if (galaxyMap.galaxyRatio) {
            // Add 20% padding to height calculation
            let desiredHeight = width * galaxyMap.galaxyRatio * 1.2;

            // Clamp Height Strict (Min 300px, Max 450px or 45vh)
            const minHeight = 350;
            // Use parent container max as hard limit if available (but it might depend on content)
            // Stricter limit: 450px Max, or 45% of view height.
            const limitHeight = Math.min(450, window.innerHeight * 0.45);
            height = Math.max(minHeight, Math.min(desiredHeight, limitHeight));
        } else {
            // Fallback strict cap
            height = Math.min(parentRect.height, 450);
        }

        canvas.width = width * dpr;
        canvas.height = height * dpr;

        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        // Recalculate transform if we have bounds
        if (galaxyMap.galaxyBounds) {
            const cx = galaxyMap.galaxyBounds.centerX;
            const cy = galaxyMap.galaxyBounds.centerY;
            const gW = galaxyMap.galaxyBounds.width;
            const gH = galaxyMap.galaxyBounds.height;

            const padding = 0.1;
            const scaleX = width / (gW * (1 + padding));
            const scaleY = height / (gH * (1 + padding));
            const optimalScale = Math.min(scaleX, scaleY, 3.0);

            galaxyMap.transform.scale = optimalScale;
            galaxyMap.transform.x = (width / 2) - (cx * optimalScale);
            galaxyMap.transform.y = (height / 2) - (cy * optimalScale);
        }

        if (galaxyMap.ctx) {
            galaxyMap.ctx.resetTransform();
            galaxyMap.ctx.scale(dpr, dpr);
        }
    };
    galaxyMap.resize = resizeInfo; // Expose for external calls
    window.addEventListener('resize', resizeInfo);
    // don't call resizeInfo() yet, wait for data or use default

    // Fetch Topology
    try {
        const data = await fetch('/api/galaxy/').then(r => r.json());
        if (data.systems && data.systems.length > 0) {
            galaxyMap.systems = data.systems.map(s => {
                if (s.total_planets === undefined) {
                    s.total_planets = (s.planets && Array.isArray(s.planets)) ? s.planets.length : 0;
                }
                return s;
            });

            // Generate lanes if missing
            if (!data.lanes || data.lanes.length === 0) {
                const laneSet = new Set();
                galaxyMap.lanes = [];
                galaxyMap.systems.forEach(s => {
                    const conns = s.connections || [];
                    conns.forEach(target => {
                        const tName = typeof target === 'string' ? target : target.name;
                        if (!tName) return;
                        const key = [s.name, tName].sort().join(':');
                        if (!laneSet.has(key)) {
                            galaxyMap.lanes.push({ source: s.name, target: tName });
                            laneSet.add(key);
                        }
                    });
                });
            } else {
                galaxyMap.lanes = data.lanes;
            }

            // Auto-Fit Logic: Pre-Calculate & Store
            if (galaxyMap.systems.length > 0) {
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;

                galaxyMap.systems.forEach(s => {
                    if (s.x < minX) minX = s.x;
                    if (s.x > maxX) maxX = s.x;
                    if (s.y < minY) minY = s.y;
                    if (s.y > maxY) maxY = s.y;
                });

                const gW = maxX - minX;
                const gH = maxY - minY;

                // Store in Global State
                galaxyMap.galaxyRatio = gH / gW;
                galaxyMap.galaxyBounds = {
                    minX, maxX, minY, maxY,
                    width: gW, height: gH,
                    centerX: minX + gW / 2,
                    centerY: minY + gH / 2
                };

                // Trigger Resize to Apply Layout
                resizeInfo();
                console.log(`[MAP] Galaxy Loaded. Aspect Ratio: ${galaxyMap.galaxyRatio.toFixed(2)}`);
            }

            // Auto-Fit Logic (REDUNDANT - DISABLED)
            if (false) {
                // 1. Calculate Bounding Box
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;

                galaxyMap.systems.forEach(s => {
                    if (s.x < minX) minX = s.x;
                    if (s.x > maxX) maxX = s.x;
                    if (s.y < minY) minY = s.y;
                    if (s.y > maxY) maxY = s.y;
                });

                // 2. Determine Galaxy Dimensions
                const galaxyWidth = maxX - minX;
                const galaxyHeight = maxY - minY;
                const centerX = minX + galaxyWidth / 2;
                const centerY = minY + galaxyHeight / 2;

                // 3. Determine Canvas Dimensions & Aspect Ratio
                const canvasWidth = canvas.clientWidth || canvas.width;

                // Calculate Desired Height based on Galaxy Aspect Ratio
                const galaxyRatio = galaxyHeight / galaxyWidth;
                // Add 20% padding to height calculation to avoid edge cramping
                let desiredHeight = canvasWidth * galaxyRatio * 1.2;

                // Clamp Height (Min 300px, Max 600px or 60vh)
                const minHeight = 350;
                const limitHeight = Math.min(600, window.innerHeight * 0.6);
                desiredHeight = Math.max(minHeight, Math.min(desiredHeight, limitHeight));

                // APPLY NEW HEIGHT
                canvas.height = desiredHeight;
                canvas.style.height = `${desiredHeight}px`;
                const canvasHeight = desiredHeight; // Update variable for scaling calc

                // 4. Calculate Scale to Fit (with 10% padding)
                const padding = 0.1;
                const scaleX = canvasWidth / (galaxyWidth * (1 + padding));
                const scaleY = canvasHeight / (galaxyHeight * (1 + padding));
                const optimalScale = Math.min(scaleX, scaleY, 3.0); // Cap max zoom

                // 5. Apply Transform
                // We want the Galaxy Center (centerX, centerY) to be at Canvas Center (canvasWidth/2, canvasHeight/2)
                // transform.x/y is the translation applied BEFORE scaling? No, usually Canvas translate -> scale
                // Formula: ScreenX = (WorldX * Scale) + TransX  (if calculate simply)
                // Let's stick to the drawGalaxyMap logic:
                // ctx.translate(transform.x, transform.y);
                // ctx.scale(transform.scale, transform.scale);
                // So: ScreenX = tx + (WorldX * scale).

                // We want: canvasWidth/2 = tx + (centerX * scale)
                // Therefore: tx = canvasWidth/2 - (centerX * scale)

                galaxyMap.transform.scale = optimalScale;
                galaxyMap.transform.x = (canvasWidth / 2) - (centerX * optimalScale);
                galaxyMap.transform.y = (canvasHeight / 2) - (centerY * optimalScale);

                console.log(`[MAP] Auto-Fit: Center(${centerX.toFixed(0)}, ${centerY.toFixed(0)}) Scale(${optimalScale.toFixed(2)})`);
            } else {
                galaxyMap.transform.x = canvas.clientWidth / 2;
                galaxyMap.transform.y = canvas.clientHeight / 2;
                galaxyMap.transform.scale = 0.5;
            }

            console.log("Galaxy Map Loaded:", data.systems.length, "systems");
        } else {
            console.log("Galaxy not ready, retrying in 2s...");
            setTimeout(initGalaxyMap, 2000);
        }
    } catch (e) {
        console.error("Failed to load galaxy map:", e);
    }

    // Interaction Listeners (Zoom/Pan)
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomSpeed = 0.1;
        const delta = e.deltaY > 0 ? (1 - zoomSpeed) : (1 + zoomSpeed);
        galaxyMap.transform.scale *= delta;
        requestAnimationFrame(drawGalaxyMap);
    });

    canvas.addEventListener('mousedown', (e) => {
        galaxyMap.isDragging = true;
        galaxyMap.lastMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mousemove', (e) => {
        if (!galaxyMap.isDragging) return;
        const dx = e.clientX - galaxyMap.lastMouse.x;
        const dy = e.clientY - galaxyMap.lastMouse.y;
        galaxyMap.transform.x += dx;
        galaxyMap.transform.y += dy;
        galaxyMap.lastMouse = { x: e.clientX, y: e.clientY };
        requestAnimationFrame(drawGalaxyMap);
    });

    window.addEventListener('mouseup', () => galaxyMap.isDragging = false);

    // Start Render Loop
    drawGalaxyLoop();
}

function drawGalaxyLoop() {
    drawGalaxyMap();
    requestAnimationFrame(drawGalaxyLoop);
}

function drawGalaxyMap() {
    const { ctx, canvas, systems, lanes, transform, animations } = galaxyMap;
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);

    // Draw Lanes
    ctx.strokeStyle = "rgba(148, 163, 184, 0.1)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    lanes.forEach(lane => {
        const s = systems.find(x => x.name === lane.source);
        const t = systems.find(x => x.name === lane.target);
        if (s && t) {
            ctx.moveTo(s.x, s.y);
            ctx.lineTo(t.x, t.y);
        }
    });
    ctx.stroke();

    // Draw Systems
    systems.forEach(sys => {
        const radius = 8; // Larger radius for visibility

        if (sys.total_planets > 0 && sys.control) {
            // Draw Pie Chart
            let startAngle = 0;
            const entries = Object.entries(sys.control);
            // Consistent order
            entries.sort((a, b) => a[0].localeCompare(b[0]));

            for (const [faction, count] of entries) {
                const sliceAngle = (count / sys.total_planets) * 2 * Math.PI;
                ctx.beginPath();
                ctx.moveTo(sys.x, sys.y);
                ctx.arc(sys.x, sys.y, radius, startAngle, startAngle + sliceAngle);
                ctx.fillStyle = getFactionColor(faction);
                ctx.fill();
                startAngle += sliceAngle;
            }
        } else {
            // Fallback
            ctx.fillStyle = getFactionColor(sys.owner);
            ctx.beginPath();
            ctx.arc(sys.x, sys.y, radius, 0, Math.PI * 2);
            ctx.fill();
        }

        // Text Label
        if (transform.scale > 0.2) {
            ctx.fillStyle = '#94a3b8';
            ctx.font = '14px Arial';
            ctx.fillText(sys.name, sys.x + 10, sys.y + 4);
        }
    });

    // Draw Animations (Explosions/Battles)
    const now = Date.now();
    for (let i = animations.length - 1; i >= 0; i--) {
        const anim = animations[i];
        const age = now - anim.startTime;
        if (age > 2000) {
            animations.splice(i, 1);
            continue;
        }

        const alpha = 1 - (age / 2000);
        const radius = 5 + (age / 100);

        ctx.beginPath();
        ctx.strokeStyle = anim.color || '#ff0000';
        ctx.lineWidth = 2;
        ctx.globalAlpha = alpha;
        ctx.arc(anim.x, anim.y, radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1.0;
    }

    ctx.restore();
}

function animateMapEvent(event, color) {
    if (!galaxyMap.systems.length) return;

    const data = event.data || {};
    const sysName = data.system_name || data.system || data.location || data.planet; // Heuristic

    // Find system coordinates (search primarily by system name, potentially planet owner system)
    // Simplified: assuming data contains System Name or we search planets
    const system = galaxyMap.systems.find(s => s.name === sysName);

    if (system) {
        galaxyMap.animations.push({
            x: system.x,
            y: system.y,
            startTime: Date.now(),
            color: color
        });
    }
}

// --- Update Logic ---

function updateLiveMetrics(metrics) {
    try {
        if (!metrics) {
            console.warn('No metrics data received');
            return;
        }

        if (metrics.turn !== undefined) {
            const turnEl = document.getElementById('metric-turn');
            if (turnEl) turnEl.innerText = metrics.turn;
        }

        // Phase 9: Process Live Galaxy Updates (Fixed)
        if (metrics.planet_status) {
            updateControlChart(metrics.planet_status);
            updateFlashpoints(metrics.planet_status);
        }

        if (metrics.planet_status && window.galaxyMap && window.galaxyMap.systems) {
            let mapChanged = false;

            // 1. Group planets by System
            const systemUpdates = {};
            metrics.planet_status.forEach(p => {
                const sName = p.system;
                if (!sName) return;

                if (!systemUpdates[sName]) systemUpdates[sName] = [];
                systemUpdates[sName].push(p);
            });

            // 2. Apply to Systems
            for (const [sysName, planets] of Object.entries(systemUpdates)) {
                const system = window.galaxyMap.systems.find(s => s.name === sysName);
                if (system) {
                    // Recalculate Control
                    const control = {};
                    let maxCount = 0;
                    let dominant = "Neutral";

                    planets.forEach(p => {
                        const own = p.owner || "Neutral";
                        control[own] = (control[own] || 0) + 1;
                    });

                    // Determine dominant
                    for (const [f, c] of Object.entries(control)) {
                        if (c > maxCount) {
                            maxCount = c;
                            dominant = f;
                        }
                    }

                    // Check for change
                    // JSON.stringify cheap check for object equality
                    if (JSON.stringify(system.control) !== JSON.stringify(control)) {
                        system.control = control;
                        mapChanged = true;
                    }

                    if (system.owner !== dominant) {
                        system.owner = dominant;
                        mapChanged = true;
                    }
                }
            }

            if (mapChanged) {
                drawGalaxyMap();
            }
        }

        // Battle Rate
        const battlesRate = metrics.battles?.rate ?? 0;
        document.getElementById('metric-bpm').innerText = battlesRate.toFixed(3) + "/s";

        // Spawn Rate
        const spawnRates = metrics.units?.spawn_rate ?? {};
        const lossRates = metrics.units?.loss_rate ?? {};
        const totalSpawn = Object.values(spawnRates || {}).reduce((a, b) => {
            // Handle nested or flat
            if (typeof b === 'object') return a + (b.navy || 0) + (b.army || 0);
            return a + b;
        }, 0);
        document.getElementById('metric-spm').innerText = (totalSpawn * 60).toFixed(1) + "/m"; // Changed to per minute for consistency? Or stick to sec? Label said Units/Sec. Let's keep /sec but fix the calc.

        updateProductionChart(spawnRates, lossRates);

        if (metrics.construction) {
            updateConstructionChart(metrics.construction.rate);
        }

        // Update Planet Summary & Flashpoints
        if (metrics.planet_status) {
            updateControlChart(metrics.planet_status);
            updateFlashpoints(metrics.planet_status);
        }
    } catch (error) {
        console.error('Error updating live metrics:', error);
    }
}

// --- Historical Mode Logic ---

async function toggleHistoricalMode(enabled) {
    isHistoricalMode = enabled;
    const modeLabel = document.getElementById('mode-label');
    const slider = document.getElementById('turn-slider');
    const turnDisplay = document.getElementById('metric-turn');

    if (enabled) {
        modeLabel.innerText = "HISTORICAL";
        modeLabel.className = "mode-hist";
        slider.disabled = false;
        turnDisplay.style.color = "var(--warning)";

        // Fetch current max turn to set slider range
        try {
            const res = await fetch('/api/run/max_turn');
            const data = await res.json();
            slider.max = data.max_turn || 1;
            slider.value = slider.max;
            handleSliderChange(slider.value);
        } catch (e) {
            console.error("Failed to fetch max turn:", e);
        }
    } else {
        modeLabel.innerText = "LIVE";
        modeLabel.className = "mode-live";
        slider.disabled = true;
        turnDisplay.style.color = "var(--accent)";
        requestSnapshot(); // Return to latest live state
    }
}

async function handleSliderChange(turn) {
    currentHistoricalTurn = parseInt(turn);
    document.getElementById('metric-turn').innerText = turn;
    loadTurnSnapshot(turn);
}

async function loadTurnSnapshot(turn) {
    try {
        const res = await fetch(`/api/snapshot/turn?turn=${turn}`);
        const data = await res.json();
        applySnapshot(data);
    } catch (e) {
        console.error("Failed to load snapshot:", e);
    }
}

function applySnapshot(data) {
    if (!data) return;

    // 1. Update Planets & Systems
    if (data.planets) {
        const planetList = Object.entries(data.planets).map(([name, info]) => ({
            name,
            system: info.system,
            owner: info.owner,
            status: info.status
        }));

        // Update Table
        updatePlanetTable(planetList);

        // Update Galaxy Map logic
        if (window.galaxyMap && window.galaxyMap.systems) {
            let mapChanged = false;

            // Group snapshot planets by system
            const systemUpdates = {};
            planetList.forEach(p => {
                const sName = p.system;
                if (!sName) return;
                if (!systemUpdates[sName]) systemUpdates[sName] = [];
                systemUpdates[sName].push(p);
            });

            // Apply updates to the map's systems
            window.galaxyMap.systems.forEach(system => {
                const planets = systemUpdates[system.name];
                if (planets) {
                    const control = {};
                    let maxCount = 0;
                    let dominant = "Neutral";

                    planets.forEach(p => {
                        const own = p.owner || "Neutral";
                        control[own] = (control[own] || 0) + 1;
                    });

                    for (const [f, c] of Object.entries(control)) {
                        if (c > maxCount) {
                            maxCount = c;
                            dominant = f;
                        }
                    }

                    if (JSON.stringify(system.control) !== JSON.stringify(control)) {
                        system.control = control;
                        mapChanged = true;
                    }

                    if (system.owner !== dominant) {
                        system.owner = dominant;
                        mapChanged = true;
                    }
                }
            });

            if (mapChanged) {
                // Ensure layout constraints are applied before drawing
                if (window.galaxyMap.resize) window.galaxyMap.resize();
                drawGalaxyMap();
            }
        }
    }

    // 2. Update Charts
    if (data.factions) {
        updateControlChart(Object.entries(data.planets).map(([name, info]) => ({
            owner: info.owner
        })));
    }
}



// Helper to update Galaxy Map from planet list (Live or Snapshot)
function updateMapWithPlanets(planetListRaw) {
    if (!window.galaxyMap || !window.galaxyMap.systems) return;

    // Normalize input (Snapshot uses object, Live uses List)
    // The incoming event.data.planets is a List of objects {name, system, owner, status}
    // applySnapshot uses Object.entries map, but let's handle List input here as per socket event
    let planets = planetListRaw;

    // Safety check if input is object (like snapshot data.planets)
    if (!Array.isArray(planetListRaw) && typeof planetListRaw === 'object') {
        planets = Object.values(planetListRaw);
    }

    let mapChanged = false;

    // Group by system
    const systemUpdates = {};
    planets.forEach(p => {
        const sName = p.system;
        if (!sName) return;
        if (!systemUpdates[sName]) systemUpdates[sName] = [];
        systemUpdates[sName].push(p);
    });

    // Apply updates
    window.galaxyMap.systems.forEach(system => {
        const pList = systemUpdates[system.name];
        if (pList) {
            const control = {};
            let maxCount = 0;
            let dominant = "Neutral";

            pList.forEach(p => {
                const own = p.owner || "Neutral";
                control[own] = (control[own] || 0) + 1;
            });

            for (const [f, c] of Object.entries(control)) {
                if (c > maxCount) {
                    maxCount = c;
                    dominant = f;
                }
            }

            // Check for changes
            if (JSON.stringify(system.control) !== JSON.stringify(control)) {
                system.control = control;
                mapChanged = true;
            }
            if (system.owner !== dominant) {
                system.owner = dominant;
                mapChanged = true;
            }
        }
    });

    if (mapChanged) {
        if (window.galaxyMap.resize) window.galaxyMap.resize();
        drawGalaxyMap();
    } else {
    }
}

function updatePlanetTable(planets) {
    const body = document.getElementById('planet-table-body');
    if (!body) return;

    body.innerHTML = '';
    planets.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
        <td>${p.system || 'N/A'} - ${p.name}</td>
            <td style="color:${getFactionColor(p.owner)}">${p.owner}</td>
            <td class="badge ${p.status ? p.status.toLowerCase() : 'stable'}">${p.status || 'Stable'}</td>
    `;
        body.appendChild(tr);
    });
}

// Dynamic Color Generator
function getCERColor(cer) {
    if (cer >= 2.0) return '#10b981'; // Green - High efficiency
    if (cer >= 1.0) return '#f59e0b'; // Yellow - Medium efficiency
    return '#ef4444'; // Red - Low efficiency
}

function getFactionColor(name) {
    if (!name) return '#666';
    if (FACTION_COLORS[name]) return FACTION_COLORS[name];

    // Hash string to color
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
    return '#' + "00000".substring(0, 6 - c.length) + c;
}

function updateControlChart(planets) {
    try {
        const chart = charts.control;
        if (!chart || !Array.isArray(planets)) return;

        // Aggregate ownership
        const counts = {};
        planets.forEach(p => {
            const owner = p.owner || 'Neutral';
            counts[owner] = (counts[owner] || 0) + 1;
        });

        const labels = Object.keys(counts);
        const data = Object.values(counts);
        const bgColors = labels.map(l => getFactionColor(l));

        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.data.datasets[0].backgroundColor = bgColors;
        chart.data.datasets[0].borderColor = "rgba(0,0,0,0.5)";

        chart.update('none'); // Smoother animation
    } catch (e) {
        console.error("Control Chart Error:", e);
    }
}

function updateFlashpoints(planets) {
    const list = document.getElementById('flashpoints-list');
    if (!list) return;

    // Filter for contested/non-stable or just changed? 
    // Data provider gives {system, owner, status}. Status usually 'Stable', 'Contested', 'Siege'.
    const hotspots = planets.filter(p => p.status && p.status !== 'Stable');

    list.innerHTML = '';

    if (hotspots.length === 0) {
        list.innerHTML = '<li class="empty-state">No Active Sieges</li>';
        return;
    }

    // Take top 5
    hotspots.slice(0, 5).forEach(p => {
        const item = document.createElement('li');
        item.className = 'flashpoint-item';
        item.innerHTML = `
        <span class="fp-sys">${p.system}</span>
            <span class="fp-status badge ${p.status.toLowerCase()}">${p.status}</span>
            <span class="fp-owner" style="color:${getFactionColor(p.owner)}">${p.owner}</span>
    `;
        list.appendChild(item);
    });
}

function updateResourceChart(event) {
    try {
        const faction = event?.faction;
        const amount = event?.data?.amount;
        const turn = event?.turn || 'Live';

        if (!faction || amount === undefined) {
            console.warn('Incomplete resource event data', event);
            return;
        }

        let chart = charts.resources;
        let dataset = chart.data.datasets.find(ds => ds.label === faction);

        if (!dataset) {
            dataset = {
                label: faction,
                borderColor: getFactionColor(faction),
                backgroundColor: getFactionColor(faction) + '20', // transparent fill
                data: [],
                fill: true,
                tension: 0.4,
                pointRadius: 0
            };
            chart.data.datasets.push(dataset);
        }

        if (!chart.data.labels.includes(turn)) {
            chart.data.labels.push(turn);
            if (chart.data.labels.length > MAX_DATA_POINTS) {
                chart.data.labels.shift();
            }
        }

        dataset.data.push(amount);
        if (dataset.data.length > MAX_DATA_POINTS) {
            dataset.data.shift();
        }

        chart.update('none');
    } catch (error) {
        console.error('Error updating resource chart:', error);
    }
}

function updateProductionChart(production, losses) {
    try {
        let chart = charts.production;
        if (!chart) return;

        hideChartLoading('productionChart'); // Ensure hidden on data update

        // Ensure defaults
        production = production || {};
        losses = losses || {};

        const factions = new Set([...Object.keys(production), ...Object.keys(losses)]);
        const labels = Array.from(factions);

        const prodData = labels.map(f => (production[f] || 0) * 60);
        const lossData = labels.map(f => (losses[f] || 0) * 60);

        // Cleanse NaN
        const cleanProd = prodData.map(v => isNaN(v) ? 0 : v);

        const colors = labels.map(f => getFactionColor(f));

        chart.data.labels = labels;

        // Update Production Dataset
        if (!chart.data.datasets[0]) {
            chart.data.datasets[0] = { label: 'Units/Min', data: [], backgroundColor: [] };
        }
        chart.data.datasets[0].data = prodData;
        chart.data.datasets[0].backgroundColor = colors;

        // Update Losses Dataset
        if (chart.data.datasets.length < 2) {
            chart.data.datasets.push({ label: 'Losses/Min', data: [], backgroundColor: '#333' });
        }
        chart.data.datasets[1].data = lossData;

        chart.update();
    } catch (error) {
        console.error('Error updating unit rates chart:', error);
    }
}

// Heatmap functions removed/replaced by Galaxy Map Canvas

// --- Chart.js Setup ---

window.initializeCharts = function () {
    console.log("Executing initializeCharts global assignment");
    try {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = '#334155';

        // Resource Trend
        const ctxRes = document.getElementById('resourceChart')?.getContext('2d');
        if (ctxRes) {
            if (charts.resources) charts.resources.destroy();
            charts.resources = new Chart(ctxRes, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: { mode: 'index', intersect: false },
                    elements: { point: { radius: 0 } },
                    scales: {
                        x: { display: false },
                        y: { display: true, beginAtZero: true, grid: { color: '#334155' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Production Bar (Updated for Stacked)
        const ctxProd = document.getElementById('productionChart')?.getContext('2d');
        if (ctxProd) {
            if (charts.production) charts.production.destroy();
            charts.production = new Chart(ctxProd, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { stacked: true, display: false },
                        y: { stacked: true, beginAtZero: true, grid: { display: false } }
                    },
                    plugins: { legend: { display: false } } // Too cramped for legend?
                }
            });
        }

        // Construction Rate (New)
        const ctxConst = document.getElementById('constructionChart')?.getContext('2d');
        if (ctxConst) {
            if (charts.construction) charts.construction.destroy();
            charts.construction = new Chart(ctxConst, {
                type: 'bar',
                data: { labels: [], datasets: [{ label: 'Completed/Min', data: [], backgroundColor: [] }] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { display: false },
                        y: { beginAtZero: true, grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Control Doughnut (New)
        const ctxCtrl = document.getElementById('controlChart')?.getContext('2d');
        if (ctxCtrl) {
            if (charts.control) charts.control.destroy();
            charts.control = new Chart(ctxCtrl, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                        legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 } } }
                    }
                }
            });
        }

        // Net Profit Chart (Line Chart)
        const ctxNetProfit = document.getElementById('netProfitChart')?.getContext('2d');
        if (ctxNetProfit) {
            if (charts.netProfit) charts.netProfit.destroy();
            charts.netProfit = new Chart(ctxNetProfit, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        x: { display: true, title: { display: true, text: 'Turn' } },
                        y: { display: true, beginAtZero: false, title: { display: true, text: 'Credits/Turn' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: 'Net Profit (Gross Income - Upkeep)' }
                    }
                }
            });
        }

        // Revenue Breakdown Chart (Stacked Area)
        const ctxRevenue = document.getElementById('revenueBreakdownChart')?.getContext('2d');
        if (ctxRevenue) {
            if (charts.revenueBreakdown) charts.revenueBreakdown.destroy();
            charts.revenueBreakdown = new Chart(ctxRevenue, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { display: true },
                        y: { display: true, stacked: true, beginAtZero: true, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: 'Revenue by Category' }
                    },
                    elements: { line: { fill: true, tension: 0.4 } }
                }
            });
        }

        // Stockpile Velocity Chart (Line with Gradient)
        const ctxVelocity = document.getElementById('stockpileVelocityChart')?.getContext('2d');
        if (ctxVelocity) {
            if (charts.stockpileVelocity) charts.stockpileVelocity.destroy();
            charts.stockpileVelocity = new Chart(ctxVelocity, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { display: true },
                        y: { display: true, beginAtZero: false, title: { display: true, text: 'Credits/Turn' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Stockpile Velocity (Growth Rate)' },
                        annotation: {
                            annotations: {
                                deathSpiral: {
                                    type: 'box',
                                    yMin: -Infinity,
                                    yMax: -500,
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    borderColor: 'rgba(239, 68, 68, 0.3)',
                                    borderWidth: 1
                                }
                            }
                        }
                    }
                }
            });
        }

        // Resource ROI Chart (Scatter Plot)
        const ctxRoi = document.getElementById('resourceRoiChart')?.getContext('2d');
        if (ctxRoi) {
            if (charts.resourceRoi) charts.resourceRoi.destroy();
            charts.resourceRoi = new Chart(ctxRoi, {
                type: 'scatter',
                data: { datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: { display: true, title: { display: true, text: 'Conquest Cost' }, grid: { color: '#334155' } },
                        y: { display: true, title: { display: true, text: 'Payback Turns' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Conquest ROI Analysis' },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const point = context.raw;
                                    return `${point.planet}: ${point.y} turns(Cost: ${point.x})`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // --- Military Charts ---

        const ctxCombatEff = document.getElementById('combatEffectivenessChart')?.getContext('2d');
        if (ctxCombatEff) {
            if (charts.combatEffectiveness) charts.combatEffectiveness.destroy();
            charts.combatEffectiveness = new Chart(ctxCombatEff, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y', // Horizontal bars
                    scales: {
                        x: { beginAtZero: true, title: { display: true, text: 'CER (Damage/Cost)' } }
                    },
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: 'Combat Effectiveness Ratio' }
                    }
                }
            });
        }


        const ctxFleetPower = document.getElementById('fleetPowerChart')?.getContext('2d');
        if (ctxFleetPower) {
            if (charts.fleetPower) charts.fleetPower.destroy();
            charts.fleetPower = new Chart(ctxFleetPower, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: true, title: { display: true, text: 'Turn' }, grid: { color: '#334155' } },
                        y: { display: true, beginAtZero: true, title: { display: true, text: 'Fleet Count' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Fleet Power Over Time (Count)' },
                        annotation: {
                            annotations: {
                                criticalZone: {
                                    type: 'box',
                                    yMin: 50,
                                    yMax: Infinity,
                                    backgroundColor: 'rgba(239, 68, 68, 0.05)',
                                    borderColor: 'rgba(239, 68, 68, 0.1)'
                                }
                            }
                        }
                    }
                }
            });
        }

        const ctxForceComp = document.getElementById('forceCompositionChart')?.getContext('2d');
        if (ctxForceComp) {
            charts.forceComposition = new Chart(ctxForceComp, {
                type: 'radar',
                data: { labels: ['Capital Ships', 'Escorts', 'Ground Units'], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { r: { beginAtZero: true, grid: { color: '#334155' }, angleLines: { color: '#334155' } } },
                    plugins: {
                        legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: 'Fleet Composition' }
                    }
                }
            });
        }

        const ctxAttrition = document.getElementById('attritionRateChart')?.getContext('2d');
        if (ctxAttrition) {
            charts.attritionRate = new Chart(ctxAttrition, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: true, title: { display: true, text: 'Turn' } },
                        y: { display: true, beginAtZero: true, title: { display: true, text: 'Attrition %' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Attrition Rate (Losses % of Army)' },
                        annotation: {
                            annotations: {
                                criticalZone: {
                                    type: 'box',
                                    yMin: 10,
                                    yMax: Infinity,
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    borderColor: 'rgba(239, 68, 68, 0.3)'
                                }
                            }
                        }
                    }
                }
            });
        }

        // Initialize canvas context for heatmap
        const heatmapCanvas = document.getElementById('battleHeatmapCanvas');
        if (heatmapCanvas) {
            // Set explicit size if needed, or rely on CSS
            heatmapCanvas.width = heatmapCanvas.offsetWidth;
            heatmapCanvas.height = heatmapCanvas.offsetHeight;

            charts.battleHeatmap = {
                canvas: heatmapCanvas,
                ctx: heatmapCanvas.getContext('2d'),
                data: []
            };
        }

        // --- Industrial & Research Charts ---

        // Industrial Density (Stacked Bar)
        const ctxIndDensity = document.getElementById('industrialDensityChart')?.getContext('2d');
        if (ctxIndDensity) {
            charts.industrialDensity = new Chart(ctxIndDensity, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: { stacked: true, beginAtZero: true, grid: { color: '#334155' } },
                        y: { stacked: true, grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: 'Industrial Density (Buildings by Type)' }
                    }
                }
            });
        }

        // Queue Efficiency (Doughnut Gauge)
        const ctxQueueEff = document.getElementById('queueEfficiencyChart')?.getContext('2d');
        if (ctxQueueEff) {
            charts.queueEfficiency = new Chart(ctxQueueEff, {
                type: 'doughnut',
                data: {
                    labels: ['Active', 'Idle'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#22c55e', '#334155'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '80%',
                    rotation: -90,
                    circumference: 180,
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: 'Construction Queue Efficiency' }
                    }
                }
            });
        }

        // Tech Tree Progress (Horizontal Stacked Bar)
        const ctxTechProgress = document.getElementById('techTreeProgressChart')?.getContext('2d');
        if (ctxTechProgress) {
            charts.techTreeProgress = new Chart(ctxTechProgress, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: { stacked: true, beginAtZero: true, grid: { color: '#334155' } },
                        y: { stacked: true, grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: 'Tech Tree Depth by Tier' }
                    }
                }
            });
        }

        // Anomaly Severity Chart (Pie/Doughnut) (Step 10)
        const ctxAnom = document.getElementById('anomalySeverityChart')?.getContext('2d');
        if (ctxAnom) {
            charts.anomalySeverity = new Chart(ctxAnom, {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'Warning', 'Info'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6'],
                        borderWidth: 1,
                        borderColor: 'rgba(255,255,255,0.1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: { position: 'right', labels: { boxWidth: 10, font: { size: 9 }, color: '#94a3b8' } },
                        title: { display: false }
                    }
                }
            });
        }

        // Territory Count Chart
        const ctxTerritory = document.getElementById('territoryCountChart')?.getContext('2d');
        if (ctxTerritory) {
            if (charts.territoryCount) charts.territoryCount.destroy();
            charts.territoryCount = new Chart(ctxTerritory, {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: true, title: { display: true, text: 'Turn' } },
                        y: { display: true, beginAtZero: true, title: { display: true, text: 'Systems Controlled' }, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Territory Control History' }
                    }
                }
            });
        }

        // Battle Stats Chart (Bar/Mixed)
        const ctxBattleStats = document.getElementById('battleStatsChart')?.getContext('2d');
        if (ctxBattleStats) {
            if (charts.battleStats) charts.battleStats.destroy();
            charts.battleStats = new Chart(ctxBattleStats, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: true },
                        y: { display: true, beginAtZero: true, grid: { color: '#334155' } }
                    },
                    plugins: {
                        legend: { display: true },
                        title: { display: true, text: 'Battle Outcomes' }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

function updateConstructionChart(rates) {
    try {
        let chart = charts.construction;
        if (!chart || !rates) return;

        const labels = Object.keys(rates);
        const data = Object.values(rates).map(v => v * 60); // Per minute
        const colors = labels.map(f => getFactionColor(f));

        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.data.datasets[0].backgroundColor = colors;

        chart.update();
    } catch (e) {
        console.error("Const Chart Error:", e);
    }
}

function updateUnitRatesChart(production, losses) {
    try {
        let chart = charts.production;
        if (!chart) return;

        production = production || {};
        losses = losses || {};

        const factions = new Set([...Object.keys(production), ...Object.keys(losses)]);
        const labels = Array.from(factions);

        // Datasets: Prod(Navy), Prod(Army), Loss(Navy), Loss(Army)
        // Check structure: is production[f] a number or object?
        // Legacy: number. New: { navy: X, army: Y }

        const getData = (source, faction, key) => {
            const val = source[faction];
            if (typeof val === 'number') {
                return key === 'army' ? val * 60 : 0; // Legacy maps to army
            }
            return (val?.[key] || 0) * 60;
        };

        const prodNavy = labels.map(f => getData(production, f, 'navy'));
        const prodArmy = labels.map(f => getData(production, f, 'army'));
        const lossNavy = labels.map(f => -getData(losses, f, 'navy')); // Negative for down
        const lossArmy = labels.map(f => -getData(losses, f, 'army'));

        // Rebuild datasets
        chart.data.labels = labels;
        chart.data.datasets = [
            { label: 'Navy Built', data: prodNavy, backgroundColor: '#60a5fa', stack: 'Stack 0' }, // Blue-ish
            { label: 'Army Built', data: prodArmy, backgroundColor: '#4ade80', stack: 'Stack 0' }, // Green-ish
            { label: 'Navy Lost', data: lossNavy, backgroundColor: '#ef4444', stack: 'Stack 0' }, // Red
            { label: 'Army Lost', data: lossArmy, backgroundColor: '#dc2626', stack: 'Stack 0' }  // Dark Red
        ];

        // Override with faction colors? No, separate by type is better for stacked. 
        // Or separate columns per faction? 
        // "x: { stacked: true }" means one bar per label (faction).
        // So this will stack all 4 on top of each other.
        // POSITIVE: Production, NEGATIVE: Losses.

        chart.update();
    } catch (error) {
        console.error('Error updating unit rates chart:', error);
    }
}

function updateNetProfitChart(data, comparisonData = null) {
    const chart = charts.netProfit;
    if (!chart || !data) return;

    chart.data.labels = data.turns;
    chart.data.datasets = [];

    // Current run datasets
    for (const [faction, metrics] of Object.entries(data.factions || {})) {
        chart.data.datasets.push({
            label: `${faction} - Gross Income`,
            data: metrics.gross_income,
            borderColor: getFactionColor(faction),
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            hidden: true // Hidden by default to reduce clutter?
        });
        chart.data.datasets.push({
            label: `${faction} - Upkeep`,
            data: metrics.upkeep,
            borderColor: getFactionColor(faction),
            backgroundColor: 'transparent',
            borderWidth: 1,
            borderDash: [5, 5],
            pointRadius: 0,
            hidden: true
        });
        chart.data.datasets.push({
            label: `${faction} - Net Profit`,
            data: metrics.net_profit,
            borderColor: getFactionColor(faction),
            backgroundColor: getFactionColor(faction) + '20',
            borderWidth: 3,
            fill: true,
            pointRadius: 0
        });
    }

    // Ghost overlay for comparison mode
    // We expect comparisonData to have same structure { factions: { ... } }
    if (comparisonData && comparisonData.factions) {
        for (const [faction, metrics] of Object.entries(comparisonData.factions)) {
            chart.data.datasets.push({
                label: `${faction} - Baseline`,
                data: metrics.net_profit,
                borderColor: getFactionColor(faction),
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [10, 5],
                opacity: 0.5,
                pointRadius: 0
            });
        }
    }

    chart.update('none');
}

function updateRevenueBreakdownChart(data) {
    const chart = charts.revenueBreakdown;
    if (!chart || !data) return;

    chart.data.labels = data.turns;
    chart.data.datasets = [];

    const categories = ['Trade', 'Tax', 'Mining', 'Conquest'];
    const categoryColors = {
        'Trade': '#10b981',
        'Tax': '#3b82f6',
        'Mining': '#f59e0b',
        'Conquest': '#ef4444'
    };

    // Check if categories exists
    if (!data.categories) return;

    Object.keys(data.categories).forEach(cat => {
        const color = categoryColors[cat] || '#888';
        chart.data.datasets.push({
            label: cat,
            data: data.categories[cat],
            borderColor: color,
            backgroundColor: color + '40',
            fill: true,
            tension: 0.4,
            pointRadius: 0
        });
    });

    chart.update('none');
}

function updateStockpileVelocityChart(data, comparisonData = null) {
    const chart = charts.stockpileVelocity;
    if (!chart || !data) return;

    chart.data.labels = data.turns;
    chart.data.datasets = [];

    for (const [faction, metrics] of Object.entries(data.factions || {})) {
        chart.data.datasets.push({
            label: faction,
            data: metrics.velocity,
            borderColor: getFactionColor(faction),
            backgroundColor: getFactionColor(faction) + '20',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0
        });
    }

    // Ghost overlay
    if (comparisonData && comparisonData.factions) {
        for (const [faction, metrics] of Object.entries(comparisonData.factions)) {
            chart.data.datasets.push({
                label: `${faction} - Baseline`,
                data: metrics.velocity,
                borderColor: getFactionColor(faction),
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [10, 5],
                opacity: 0.5,
                pointRadius: 0
            });
        }
    }

    chart.update('none');
}

function updateResourceRoiChart(data) {
    const chart = charts.resourceRoi;
    if (!chart || !data) return;

    chart.data.datasets = [];

    // Group by faction
    const byFaction = {};
    if (Array.isArray(data)) {
        data.forEach(point => {
            if (!byFaction[point.faction]) byFaction[point.faction] = [];
            byFaction[point.faction].push({
                x: point.cost,
                y: point.payback_turns,
                planet: point.planet
            });
        });
    }

    for (const [faction, points] of Object.entries(byFaction)) {
        chart.data.datasets.push({
            label: faction,
            data: points,
            backgroundColor: getFactionColor(faction),
            borderColor: getFactionColor(faction),
            pointRadius: 6,
            pointHoverRadius: 8
        });
    }

    chart.update('none');
}

function getSkeletonId(chartId) {
    // Handle both "resourceChart" and "resources" input variations if necessary
    // Currently chartId passed in is usually "resourceChart" (from showChartLoading calls)
    let base = chartId.replace('Chart', '').replace('Canvas', '');

    // Mapping for irregularities
    const map = {
        'resource': 'resources',
        'unitRates': 'production', // Production chart sometimes called unitRatesChart in legacy
        'battleHeatmap': 'battleHeatmap'
    };

    base = map[base] || base;
    return `skeleton-${base}`;
}

function showChartLoading(chartId) {
    const skeletonId = getSkeletonId(chartId);
    const skeleton = document.getElementById(skeletonId);
    const canvas = document.getElementById(chartId);

    if (skeleton) skeleton.classList.remove('hidden');
    if (canvas) canvas.classList.add('hidden');
}

function hideChartLoading(chartId) {
    const skeletonId = getSkeletonId(chartId);
    const skeleton = document.getElementById(skeletonId);
    const canvas = document.getElementById(chartId);

    if (skeleton) skeleton.classList.add('hidden');
    if (canvas) canvas.classList.remove('hidden');

    if (canvas) {
        const parent = canvas.parentElement;
        if (parent) {
            parent.style.opacity = '1';
            parent.style.pointerEvents = 'auto';
            // Remove error overlay if exists
            const err = parent.querySelector('.chart-error-overlay');
            if (err) err.remove();
        }
    }
}

// --- Error Handling & Logging (Step 3 & 4) ---

function logDashboardError(context, error, details = {}) {
    debugLog('ERROR', `${context}: ${error.message || error}`, details);

    // Also track in history
    const errorEntry = {
        timestamp: new Date().toISOString(),
        context,
        error: error.message || error,
        stack: error.stack,
        details
    };

    if (window.DASHBOARD_DEBUG) console.error(error);
}

function showUserError(message, details = null, action = null) {
    const container = document.getElementById('global-error-container');
    if (!container) return; // Should create this in HTML step

    const msg = document.createElement('div');
    msg.className = 'error-toast';
    msg.innerHTML = `
        <div class="error-content">
            <strong>Error:</strong> ${message}
            ${details ? `<br><small>${details}</small>` : ''}
        </div>
        <button class="close-btn" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(msg);

    // Auto remove after 5s unless critical
    setTimeout(() => msg.remove(), 8000);
}




// --- Pagination & Data Fetching (Step 12) ---
function handlePageChange(id, page) {
    if (id === 'alerts') {
        const type = document.getElementById('alert-type-filter')?.value || 'all';
        const severity = document.getElementById('alert-severity-filter')?.value || 'all';
        const history = document.getElementById('alert-history-toggle')?.checked || false;
        loadAlertData(type, severity, history, page);
    } else if (id === 'telemetry') {
        loadTelemetryData(page);
    }
}

async function loadTelemetryData(page = 1) {
    try {
        const limit = pagination.telemetry.pageSize;
        const offset = (page - 1) * limit;
        const url = `/api/metrics/paginated?table=telemetry&universe=${currentUniverse}&limit=${limit}&offset=${offset}`;

        const res = await fetchWithLogging(url);
        const data = await res.json();

        pagination.telemetry.currentPage = page;
        pagination.telemetry.update(data.total || 0);

        const list = document.getElementById('event-log');
        if (list) {
            list.innerHTML = '';
            (data.items || []).forEach(item => logEvent(item, true));
        }
    } catch (e) {
        console.error("Telemetry pagination failed:", e);
    }
}

async function fetchResourceHistory(faction = 'all') {
    showChartLoading('resourceChart');
    try {
        const { min, max } = globalFilters.turnRange;
        const range = max - min;
        const downsample = range > 1000 ? 1000 : null;
        const dsParam = downsample ? `&downsample=${downsample}` : '';
        const url = `/api/metrics/historical?universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentRunId}&faction=${faction}&min_turn=${min}&max_turn=${max}${dsParam}`;

        const res = await fetchWithLogging(url);
        const data = await res.json();

        if (data.factions) {
            Object.entries(data.factions).forEach(([f, history]) => {
                populateResourceHistory(f, history);
            });
        }
    } catch (e) {
        console.error("Resource history fetch failed:", e);
    } finally {
        hideChartLoading('resourceChart');
    }
}

function logEvent(event, isBulk = false) {
    const list = document.getElementById('event-log');
    if (!list) return;

    const li = document.createElement('li');
    li.className = `log-item ${event.severity || 'info'}`;
    const time = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

    let icon = 'ℹ️';
    if (event.type === 'battle') icon = '⚔️';
    if (event.type === 'economic') icon = '💰';
    if (event.type === 'research') icon = '🧪';
    if (event.type === 'alert') icon = '⚠️';

    let message = event.message || event.text;

    if (!message) {
        // Construct message from structured telemetry
        const type = event.event_type || 'Unknown';
        const cat = event.category || 'System';
        const faction = event.faction ? `[${event.faction}] ` : '';

        let details = '';
        const d = event.data || {};

        if (d.planet || d.location) details += ` @ ${d.planet || d.location}`;
        if (d.system) details += ` in ${d.system}`;
        if (d.unit) details += ` (${d.unit})`;
        if (d.building) details += ` - ${d.building}`;
        if (d.tech_id) details += ` - ${d.tech_id}`;
        if (d.amount) details += ` (${d.amount})`;

        message = `${faction}${cat}: ${type}${details}`;
    }

    li.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-icon">${icon}</span>
        <span class="log-message">${message}</span>
    `;

    if (isBulk) {
        list.appendChild(li);
    } else {
        list.insertBefore(li, list.firstChild);
        if (list.children.length > 50) list.removeChild(list.lastChild);
    }
}

// --- Lazy Loading (Step 9) ---
async function loadChartDataLazily(chartId) {
    const loaders = {
        'resources': () => fetchResourceHistory('all'),
        'production': loadIndustrialData,
        'netProfit': loadEconomicData,
        'revenueBreakdown': loadEconomicData,
        'stockpileVelocity': loadEconomicData,
        'resourceRoi': loadEconomicData,
        'combatEffectiveness': loadMilitaryData,
        'fleetPower': loadFleetPowerData,
        'territoryCount': loadTerritoryData,
        'battleStats': loadBattleStatsData,
        'forceComposition': loadMilitaryData,
        'attritionRate': loadMilitaryData,
        'battleHeatmap': loadMilitaryData,
        'industrialDensity': loadIndustrialData,
        'queueEfficiency': loadIndustrialData,
        'techTreeProgress': loadTechData,
        'anomalySeverity': loadAlertData
    };

    if (loaders[chartId]) {
        await loaders[chartId]();
    }
}

// --- Performance Panel (Step 11) ---
function togglePerformancePanel() {
    const panel = document.getElementById('performance-panel');
    const icon = document.getElementById('perf-toggle-icon');
    if (!panel) return;

    if (panel.classList.contains('collapsed')) {
        panel.classList.remove('collapsed');
        icon.textContent = '▲';
        startPerformancePolling();
    } else {
        panel.classList.add('collapsed');
        icon.textContent = '▼';
        stopPerformancePolling();
    }
}

let perfInterval = null;
function startPerformancePolling() {
    if (perfInterval) return;
    refreshPerformanceStats();
    perfInterval = setInterval(refreshPerformanceStats, 5000);
}

function stopPerformancePolling() {
    clearInterval(perfInterval);
    perfInterval = null;
}

async function refreshPerformanceStats() {
    const spinner = document.getElementById('perf-spinner');
    if (spinner) spinner.style.display = 'block';

    try {
        const res = await fetchWithLogging('/api/performance/stats');
        const stats = await res.json();

        const memEl = document.getElementById('perf-mem');
        if (memEl) memEl.textContent = `${Math.round(stats.memory?.rss / 1024 / 1024) || '--'} MB`;

        const cacheEl = document.getElementById('perf-cache');
        if (cacheEl) cacheEl.textContent = `${(stats.cache?.hit_rate * 100 || 0).toFixed(1)}%`;

        const slowEl = document.getElementById('perf-slow-count');
        if (slowEl) slowEl.textContent = `${stats.profiling?.slow_queries || 0} Detected`;

        const profilingBtn = document.getElementById('profiling-btn');
        if (profilingBtn) {
            if (stats.profiling_enabled) {
                profilingBtn.textContent = 'DISABLE';
                profilingBtn.classList.add('btn-accent');
                profilingBtn.classList.remove('btn-outline');
            } else {
                profilingBtn.textContent = 'ENABLE';
                profilingBtn.classList.remove('btn-accent');
                profilingBtn.classList.add('btn-outline');
            }
        }
    } catch (e) {
        console.error("Failed to load performance stats:", e);
    } finally {
        if (spinner) spinner.style.display = 'none';
    }
}

async function toggleProfiling(e) {
    if (e) e.stopPropagation();
    const btn = document.getElementById('profiling-btn');
    const enabling = btn.textContent === 'ENABLE';
    const endpoint = enabling ? 'enable' : 'disable';

    try {
        await fetchWithLogging(`/api/performance/profiling/${endpoint}`, { method: 'POST' });
        refreshPerformanceStats();
    } catch (err) {
        console.error("Profiling toggle failed:", err);
    }
}

// --- Military Analysis Functions ---

// --- Military Analysis Functions ---

async function loadMilitaryData() {
    showChartLoading('combatEffectivenessChart');
    showChartLoading('forceCompositionChart');
    showChartLoading('attritionRateChart');
    showChartLoading('battleHeatmapCanvas');

    try {
        const factions = globalFilters.selectedFactions.join(',');
        const { min, max } = globalFilters.turnRange;
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&min_turn=${min}&max_turn=${max}`;

        // Load combat effectiveness
        const cerRes = await fetchWithLogging(`/api/military/combat_effectiveness?${query}`);
        const cerData = await cerRes.json();
        updateCombatEffectivenessChart(cerData, comparisonModeEnabled ? ghostData.cer : null);

        // Load force composition (primary selection)
        const primaryFaction = globalFilters.selectedFactions[0] || 'all';
        if (primaryFaction !== 'all') {
            const compRes = await fetchWithLogging(`/api/military/force_composition?${query}&faction=${primaryFaction}`);
            const compData = await compRes.json();
            updateForceCompositionChart(compData, primaryFaction);
        } else {
            updateForceCompositionChart(null, null);
        }

        // Load attrition rate
        const attritionRes = await fetchWithLogging(`/api/military/attrition_rate?${query}`);
        const attritionData = await attritionRes.json();
        updateAttritionRateChart(attritionData, comparisonModeEnabled ? ghostData.attrition : null);

        // Load battle heatmap
        const heatmapRes = await fetchWithLogging(`/api/military/battle_heatmap?${query}`);
        const heatmapData = await heatmapRes.json();
        drawBattleHeatmap(heatmapData);

    } catch (error) {
        console.error('Failed to load military data:', error);
        showChartError('combatEffectivenessChart', 'Failed to load military data');
        showChartError('forceCompositionChart', 'Failed to load composition');
        showChartError('attritionRateChart', 'Failed to load attrition');
    } finally {
        hideChartLoading('combatEffectivenessChart');
        hideChartLoading('forceCompositionChart');
        hideChartLoading('attritionRateChart');
        hideChartLoading('battleHeatmapCanvas');
    }
}

async function loadFleetPowerData() {
    showChartLoading('fleetPowerChart');
    try {
        const query = getQueryString();
        const res = await fetchWithLogging(`/api/military/fleet_power?${query}`);
        if (!res.ok) throw new Error(`API Error ${res.status}`);
        const data = await res.json();

        // Update function needed for fleet power
        updateFleetPowerChart(data, comparisonModeEnabled ? ghostData.fleetPower : null);
    } catch (e) {
        console.error("Fleet power load failed:", e);
        showChartError('fleetPowerChart', "Failed to load fleet power.");
    } finally {
        hideChartLoading('fleetPowerChart');
    }
}

async function loadTerritoryData() {
    showChartLoading('territoryCountChart');
    try {
        const query = getQueryString();
        const res = await fetchWithLogging(`/api/military/territory_count?${query}`);
        if (!res.ok) throw new Error(`API Error ${res.status}`);
        const data = await res.json();

        updateTerritoryCountChart(data);
    } catch (e) {
        console.error("Territory load failed:", e);
        showChartError('territoryCountChart', "Failed to load territory data.");
    } finally {
        hideChartLoading('territoryCountChart');
    }
}

async function loadBattleStatsData() {
    showChartLoading('battleStatsChart');
    try {
        const query = getQueryString();
        const res = await fetchWithLogging(`/api/military/battle_stats?${query}`);
        if (!res.ok) throw new Error(`API Error ${res.status}`);
        const data = await res.json();

        updateBattleStatsChart(data);
    } catch (e) {
        console.error("Battle stats load failed:", e);
        showChartError('battleStatsChart', "Failed to load battle stats.");
    } finally {
        hideChartLoading('battleStatsChart');
    }
}

// Map tech data loader to research data
const loadTechData = loadResearchData;

function getQueryString() {
    const { min, max } = globalFilters.turnRange;
    const factions = globalFilters.selectedFactions.join(',');
    return `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&min_turn=${min}&max_turn=${max}`;
}

// Update Chart Functions for new types
function updateFleetPowerChart(data, comparisonData = null) {
    const chart = charts.fleetPower;
    if (!chart || !data) return;

    chart.data.labels = data.turns || [];
    chart.data.datasets = [];

    const factions = data.factions || {};
    Object.keys(factions).forEach(f => {
        chart.data.datasets.push({
            label: f,
            data: factions[f],
            borderColor: getFactionColor(f),
            backgroundColor: 'transparent',
            tension: 0.3,
            pointRadius: 0
        });
    });

    chart.update();
}

function updateTerritoryCountChart(data) {
    const chart = charts.territoryCount;
    if (!chart || !data) return;

    chart.data.labels = data.turns || [];
    chart.data.datasets = [];

    const factions = data.factions || {};
    Object.keys(factions).forEach(f => {
        chart.data.datasets.push({
            label: f,
            data: factions[f],
            borderColor: getFactionColor(f),
            backgroundColor: 'transparent',
            tension: 0.1,
            pointRadius: 0
        });
    });
    chart.update();
}

function updateBattleStatsChart(data) {
    const chart = charts.battleStats;
    if (!chart || !data) return;

    // Example: Wins/Losses per faction
    const labels = Object.keys(data.factions || {});
    const wins = labels.map(f => data.factions[f].wins || 0);
    const losses = labels.map(f => data.factions[f].losses || 0);

    chart.data.labels = labels;
    chart.data.datasets = [
        { label: 'Wins', data: wins, backgroundColor: '#10b981' },
        { label: 'Losses', data: losses, backgroundColor: '#ef4444' }
    ];
    chart.update();
}

function showChartError(chartId, message) {
    const base = chartId.replace('Chart', '').replace('Canvas', '');
    // Try to find container by data-chart-id
    const container = document.querySelector(`[data-chart-id="${base}"]`);

    if (container) {
        // Check if error overlay already exists
        let errorOverlay = container.querySelector('.chart-error-overlay');
        if (!errorOverlay) {
            errorOverlay = document.createElement('div');
            errorOverlay.className = 'chart-error-overlay';
            errorOverlay.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.8);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#ef4444;text-align:center;z-index:10;';
            container.appendChild(errorOverlay);
        }

        errorOverlay.innerHTML = `
            <span style="font-size:2rem;margin-bottom:0.5rem">⚠️</span>
            <p style="font-size:0.9rem;margin:0">${message}</p>
            <button onclick="loadChartDataLazily('${base}')" style="margin-top:0.5rem;padding:0.25rem 0.5rem;background:#334155;border:1px solid #475569;color:#fff;border-radius:4px;cursor:pointer;">Retry</button>
        `;
    }
}

function updateCombatEffectivenessChart(data, comparisonData = null) {
    const chart = charts.combatEffectiveness;
    if (!chart || !data) return;

    chart.data.labels = [];
    chart.data.datasets = [];

    let factions = [];
    let cerValues = [];

    if (data.factions) {
        factions = Object.keys(data.factions);
        cerValues = Object.values(data.factions).map(d => d.cer);
    } else if (data.cer) {
        // Fallback for different API shape
        factions = Object.keys(data.cer);
        cerValues = Object.values(data.cer);
    }

    const colors = factions.map(f => getFactionColor(f));

    chart.data.labels = factions;
    chart.data.datasets.push({
        label: 'Combat Effectiveness (Damage/Cost)',
        data: cerValues,
        backgroundColor: colors,
        barPercentage: 0.6
    });

    // Ghost Overlay
    if (comparisonData && (comparisonData.factions || comparisonData.cer)) {
        let ghostValues = [];
        if (comparisonData.factions) {
            ghostValues = factions.map(f => comparisonData.factions[f]?.cer || 0);
        } else {
            ghostValues = factions.map(f => comparisonData.cer?.[f] || 0);
        }

        chart.data.datasets.push({
            label: 'Baseline (Ghost)',
            data: ghostValues,
            backgroundColor: 'transparent',
            borderColor: '#94a3b8',
            borderWidth: 1,
            borderDash: [5, 5],
            type: 'bar',
            grouped: false,
            barPercentage: 0.4
        });
    }

    chart.update('none');
}

function updateForceCompositionChart(data, selectedFaction) {
    const chart = charts.forceComposition;
    if (!chart) return;

    chart.data.datasets = [];

    if (!data || !selectedFaction) {
        chart.update();
        return;
    }

    const values = [
        data.capital_ships || 0,
        data.escorts || 0,
        data.ground_units || 0
    ];

    chart.data.datasets.push({
        label: selectedFaction,
        data: values,
        backgroundColor: getFactionColor(selectedFaction) + '40',
        borderColor: getFactionColor(selectedFaction),
        borderWidth: 2,
        pointRadius: 4
    });

    chart.update();
}

function updateAttritionRateChart(data, comparisonData = null) {
    const chart = charts.attritionRate;
    if (!chart || !data) return;

    chart.data.datasets = [];
    let allTurns = new Set();

    const addDataset = (faction, turns, rates, isGhost = false) => {
        turns.forEach(t => allTurns.add(t));

        chart.data.datasets.push({
            label: isGhost ? `${faction} (Baseline)` : faction,
            data: turns.map((t, i) => ({ x: t, y: rates[i] })),
            borderColor: isGhost ? '#94a3b8' : getFactionColor(faction),
            backgroundColor: 'transparent',
            borderWidth: isGhost ? 1 : 2,
            borderDash: isGhost ? [5, 5] : [],
            pointRadius: 0
        });
    };

    if (data.factions) {
        for (const [f, d] of Object.entries(data.factions)) {
            addDataset(f, d.turns, d.attrition_rate);
        }
    } else if (data.turns) {
        addDataset("Current", data.turns, data.attrition_rate);
    }

    if (comparisonData && comparisonData.factions) {
        for (const [f, d] of Object.entries(comparisonData.factions)) {
            if (data.factions && data.factions[f]) {
                addDataset(f, d.turns, d.attrition_rate, true);
            }
        }
    }

    // Sort turns
    chart.data.labels = Array.from(allTurns).sort((a, b) => a - b);

    chart.update('none');
}

function drawBattleHeatmap(data) {
    const chart = charts.battleHeatmap;
    if (!chart || !chart.ctx) return;

    const ctx = chart.ctx;
    const canvas = chart.canvas;
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    if (!data || data.length === 0) return;

    const systemMap = {};
    if (galaxyMap && galaxyMap.systems) {
        galaxyMap.systems.forEach(s => {
            systemMap[s.name] = { x: s.x, y: s.y };
        });
    }

    data.forEach(point => {
        const sys = systemMap[point.system];
        if (!sys) return;

        const scale = Math.min(width, height) / 1200;
        const cx = width / 2;
        const cy = height / 2;

        const px = cx + (sys.x * scale);
        const py = cy + (sys.y * scale);

        const cer = point.cer;
        const count = point.battle_count;

        const color = getCERColor(cer);

        ctx.beginPath();
        ctx.arc(px, py, Math.max(2, Math.min(20, count * 2)), 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.6;
        ctx.fill();
        ctx.lineWidth = 0.5;
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        if (count > 5) {
            ctx.fillStyle = '#fff';
            ctx.font = '10px Arial';
            ctx.fillText(point.system, px + 5, py);
        }
    });
}

// --- Development Pulse Update Functions ---

function updateIndustrialDensityChart(data, comparisonData = null, factionHint = null) {
    const chart = charts.industrialDensity;
    if (!chart || !data) return;

    // Handle both {factions: {...}} and single-faction responses
    let factionNames = [];
    let factionDataMap = {};

    if (data.factions) {
        factionNames = Object.keys(data.factions);
        factionDataMap = data.factions;
    } else {
        const foundFaction = factionHint || data.faction || "Current";
        factionNames = [foundFaction];
        factionDataMap[foundFaction] = data;
    }

    if (factionNames.length === 0) return;

    chart.data.labels = factionNames;
    const buildingTypes = ['Military', 'Economy', 'Research'];
    const colors = {
        'Military': '#ef4444',
        'Economy': '#22c55e',
        'Research': '#3b82f6'
    };

    chart.data.datasets = buildingTypes.map(type => ({
        label: type,
        data: factionNames.map(f => {
            const fData = factionDataMap[f];
            return fData.building_counts ? fData.building_counts[type] || 0 : 0;
        }),
        backgroundColor: colors[type],
        stack: 'current'
    }));

    if (comparisonData) {
        buildingTypes.forEach(type => {
            chart.data.datasets.push({
                label: `${type} (Baseline)`,
                data: factionNames.map(f => {
                    const cData = (comparisonData.factions ? comparisonData.factions[f] : comparisonData.building_counts ? comparisonData : null);
                    if (!cData) return 0;
                    return cData.building_counts ? cData.building_counts[type] || 0 : 0;
                }),
                backgroundColor: colors[type] + '40', // 25% opacity
                stack: 'baseline'
            });
        });
    }

    chart.update();
}

function updateQueueEfficiencyChart(data) {
    const chart = charts.queueEfficiency;
    if (!chart || !data) return;

    const idlePct = data.idle_percentage !== undefined ? data.idle_percentage : (1 - (data.avg_queue_efficiency || 0));

    chart.data.datasets[0].data = [(1 - idlePct) * 100, idlePct * 100];

    // Color coding based on IDLE percentage thresholds
    let color = '#22c55e'; // Green (< 10%)
    if (idlePct > 0.1) color = '#eab308'; // Yellow (10-30%)
    if (idlePct > 0.3) color = '#ef4444'; // Red (> 30%)

    chart.data.datasets[0].backgroundColor = [color, '#334155'];
    chart.update();

    // Update center text (requires plugin or manual DOM)
    const container = document.getElementById('queueEfficiencyChart')?.parentElement;
    if (container) {
        let label = container.querySelector('.gauge-label');
        if (!label) {
            label = document.createElement('div');
            label.className = 'gauge-label';
            label.style.position = 'absolute';
            label.style.top = '60%';
            label.style.left = '50%';
            label.style.transform = 'translate(-50%, -50%)';
            label.style.fontSize = '1.5rem';
            label.style.fontWeight = 'bold';
            container.style.position = 'relative';
            container.appendChild(label);
        }
        label.textContent = `${Math.round(idlePct * 100)}% Idle`;
        label.style.color = color;
    }
}

function updateTechTreeProgressChart(data, comparisonData = null, factionHint = null) {
    const chart = charts.techTreeProgress;
    if (!chart || !data) return;

    let factionNames = [];
    let factionDataMap = {};

    if (data.factions) {
        factionNames = Object.keys(data.factions);
        factionDataMap = data.factions;
    } else {
        const foundFaction = factionHint || data.faction || "Current";
        factionNames = [foundFaction];
        factionDataMap[foundFaction] = data;
    }

    if (factionNames.length === 0) return;

    chart.data.labels = factionNames;

    // Identify all tiers across all factions
    const tiers = new Set();
    factionNames.forEach(f => {
        const techs = factionDataMap[f].techs_by_tier || {};
        Object.keys(techs).forEach(t => tiers.add(t));
    });
    const sortedTiers = Array.from(tiers).sort();

    const tierColors = [
        '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'
    ];

    chart.data.datasets = sortedTiers.map((tier, i) => ({
        label: `Tier ${tier} `,
        data: factionNames.map(f => (factionDataMap[f].techs_by_tier || {})[tier] || 0),
        backgroundColor: tierColors[i % tierColors.length],
        stack: 'current'
    }));

    if (comparisonData) {
        sortedTiers.forEach((tier, i) => {
            chart.data.datasets.push({
                label: `Tier ${tier} (Baseline)`,
                data: factionNames.map(f => {
                    const cData = (comparisonData.factions ? comparisonData.factions[f] : comparisonData.techs_by_tier ? comparisonData : null);
                    if (!cData) return 0;
                    return (cData.techs_by_tier || {})[tier] || 0;
                }),
                backgroundColor: tierColors[i % tierColors.length] + '40',
                stack: 'baseline'
            });
        });
    }

    chart.update();
}

function updateResearchRoiCards(data) {
    const container = document.getElementById('researchRoiContainer');
    if (!container) return;

    container.innerHTML = '';

    const results = Array.isArray(data) ? data : [data];
    if (results.length === 0 || results[0].error) {
        container.innerHTML = '<div class="text-slate-400 text-center p-4">No recent research ROI data available</div>';
        return;
    }

    results.forEach(roi => {
        const card = document.createElement('div');
        card.className = 'bg-slate-800/50 p-3 rounded border border-slate-700 mb-2';

        const scoreColor = roi.roi_score > 1.0 ? 'text-green-400' : (roi.roi_score > 0.5 ? 'text-yellow-400' : 'text-red-400');

        card.innerHTML = `
        <div class="flex justify-between items-start mb-2">
                <h4 class="font-bold text-sm">${roi.tech_name || roi.tech_id}</h4>
                <span class="px-2 py-0.5 rounded text-xs bg-slate-700 ${scoreColor}">ROI: ${roi.roi_score.toFixed(2)}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                    <div class="text-slate-400">Production Impact</div>
                    <div class="${roi.after_metrics?.prod_rate > roi.before_metrics?.prod_rate ? 'text-green-400' : 'text-slate-300'}">
                        ${roi.before_metrics?.prod_rate?.toFixed(2) || 0} → ${roi.after_metrics?.prod_rate?.toFixed(2) || 0}
                    </div>
                </div>
                <div>
                    <div class="text-slate-400">Income Impact</div>
                    <div class="${roi.after_metrics?.income > roi.before_metrics?.income ? 'text-green-400' : 'text-slate-300'}">
                        ${roi.before_metrics?.income?.toFixed(2) || 0} → ${roi.after_metrics?.income?.toFixed(2) || 0}
                    </div>
                </div>
            </div>
            <div class="mt-2 text-[10px] text-slate-500 italic">Category: ${roi.impact_category || 'General'}</div>
    `;
        container.appendChild(card);
    });
}

function updateConstructionTimeline(milestones) {
    const list = document.getElementById('constructionTimelineList');
    if (!list) return;

    list.innerHTML = '';
    if (!milestones || milestones.length === 0) {
        list.innerHTML = '<li class="text-slate-500 text-xs p-2">Waiting for construction events...</li>';
        return;
    }

    milestones.forEach(m => {
        const li = document.createElement('li');
        li.className = 'flex items-center gap-2 p-2 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors';
        li.innerHTML = `
        <span class="text-[10px] bg-slate-700 px-1 rounded text-slate-400">T${m.turn}</span>
            <span class="w-2 h-2 rounded-full" style="background-color: ${getFactionColor(m.faction)}"></span>
            <span class="text-xs text-slate-200">Built <b>${m.building_type}</b> on <b>${m.planet}</b></span>
    `;
        list.appendChild(li);
    });
}

function updateResearchTimeline(milestones) {
    const list = document.getElementById('tech-timeline-list');
    if (!list) return;

    list.innerHTML = '';
    if (!milestones || milestones.length === 0) {
        list.innerHTML = '<li class="text-slate-500 text-xs p-2">Waiting for research events...</li>';
        return;
    }

    milestones.forEach(m => {
        const li = document.createElement('li');
        li.className = 'flex items-center gap-2 p-2 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors';
        li.innerHTML = `
        <span class="text-[10px] bg-slate-700 px-1 rounded text-slate-400">T${m.turn}</span>
            <span class="w-2 h-2 rounded-full" style="background-color: ${getFactionColor(m.faction)}"></span>
            <span class="text-xs text-slate-200">Unlocked <b>${m.tech_name}</b> <span class="text-[10px] text-blue-400">(Tier ${m.tier})</span></span>
    `;
        list.appendChild(li);
    });
}


// --- Alert Management (Step 9) ---

async function loadAlertData(filterType = 'all', filterSeverity = 'all', showHistory = false, page = 1) {
    try {
        const universe = currentUniverse;
        const limit = pagination.alerts.pageSize;
        const offset = (page - 1) * limit;

        const url = `/api/metrics/paginated?table=alerts&universe=${universe}&type=${filterType}&severity=${filterSeverity}&limit=${limit}&offset=${offset}`;

        const [data, summary] = await Promise.all([
            fetchWithLogging(url).then(r => r.json()),
            fetchWithLogging(`/api/alerts/summary?universe=${universe}`).then(r => r.json())
        ]);

        pagination.alerts.currentPage = page;
        pagination.alerts.update(data.total || 0);

        updateAlertsList(data.items || []);
        updateAlertSummaryUI(summary);
        updateAnomalySummaryChart(summary);
    } catch (e) {
        console.error("Failed to load alerts:", e);
    }
}

function updateAlertsList(alerts) {
    const list = document.getElementById('active-alerts-list');
    if (!list) return;

    if (!alerts || alerts.length === 0) {
        list.innerHTML = '<div class="empty-state">No active anomalies detected in sector.</div>';
        document.getElementById('alert-pulse')?.classList.add('hidden');
        return;
    }

    document.getElementById('alert-pulse')?.classList.remove('hidden');

    list.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}" id="alert-${alert.id}">
            <div class="alert-info">
                <span class="alert-msg">${alert.message}</span>
                <span class="alert-meta">${alert.rule_name} | Turn ${alert.context ? (alert.context.turn || '??') : '??'} | ${new Date(alert.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="alert-actions">
                <button class="btn-ack" onclick="acknowledgeAlert('${alert.id}')">ACK</button>
            </div>
        </div>
        `).join('');
}

function updateAlertSummaryUI(summary) {
    const crit = document.getElementById('alert-summary-critical');
    const warn = document.getElementById('alert-summary-warning');

    if (crit) crit.textContent = `${summary.by_severity?.critical || 0} CRITICAL`;
    if (warn) warn.textContent = `${summary.by_severity?.warning || 0} WARNING`;
}

function updateAnomalySummaryChart(summary) {
    const chart = charts.anomalySeverity;
    if (!chart) return;

    const data = [
        summary.by_severity?.critical || 0,
        summary.by_severity?.warning || 0,
        summary.by_severity?.info || 0
    ];

    chart.data.datasets[0].data = data;
    chart.update();
}

async function acknowledgeAlert(alertId) {
    try {
        const res = await fetchWithLogging(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
        if (res.ok) {
            const item = document.getElementById(`alert-${alertId}`);
            if (item) {
                item.style.opacity = '0.4';
                item.querySelector('.btn-ack').disabled = true;
            }
        }
    } catch (e) {
        console.error("Failed to acknowledge alert:", e);
    }
}

function applyAlertFilters() {
    const type = document.getElementById('alert-type-filter').value;
    const severity = document.getElementById('alert-severity-filter').value;
    const history = document.getElementById('alert-history-toggle').checked;
    loadAlertData(type, severity, history);
}

function refreshAllCharts() {
    loadEconomicData();
    loadMilitaryData();
    loadDevelopmentPulseData();
}

// --- Export Logic ---
async function exportCurrentView(format) {
    const overlay = document.getElementById('export-overlay');
    const status = document.getElementById('export-status');
    const progress = document.getElementById('export-progress');

    if (overlay) overlay.classList.remove('hidden');
    if (status) status.innerText = `GENERATING ${format.toUpperCase()} EXPORT...`;
    if (progress) progress.style.width = '10%';

    try {
        // Collect visible metrics (Comment 2)
        const metrics = Object.entries(globalFilters.visibleMetrics)
            .filter(([_, visible]) => visible)
            .map(([key, _]) => key);

        const payload = {
            universe: currentUniverse,
            run_id: currentRunId,
            batch_id: currentBatchId,
            factions: globalFilters.selectedFactions,
            turn_range: globalFilters.turnRange,
            metrics: metrics,
            format: format
        };

        const endpoint = format === 'pdf' ? '/api/reports/export/metrics/pdf' : '/api/reports/export/metrics';

        if (progress) progress.style.width = '40%';

        const response = await fetchWithLogging(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Export failed');
        }

        if (progress) progress.style.width = '70%';

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const filename = `export_${currentRunId}_${timestamp}.${format === 'excel' ? 'xlsx' : format}`;

        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        if (progress) progress.style.width = '100%';
        if (status) status.innerText = "EXPORT COMPLETE!";

    } catch (error) {
        console.error('Export failed:', error);
        if (status) status.innerText = "EXPORT FAILED: " + error.message;
        if (progress) {
            progress.style.width = '100%';
            progress.style.backgroundColor = 'var(--error)';
        }
    } finally {
        setTimeout(() => {
            if (overlay) overlay.classList.add('hidden');
            if (progress) {
                progress.style.width = '0%';
                progress.style.backgroundColor = 'var(--accent)';
            }
        }, 1500);
    }
}

// --- Bookmark Manager ---
function openBookmarkManager() {
    const modal = document.getElementById('bookmark-modal');
    if (modal) modal.classList.remove('hidden');
    loadBookmarks();
}

function closeBookmarkManager() {
    const modal = document.getElementById('bookmark-modal');
    if (modal) modal.classList.add('hidden');
}

function saveBookmark() {
    const nameInput = document.getElementById('bookmark-name');
    const name = nameInput.value.trim();
    if (!name) return alert("Please enter a bookmark name.");

    const bookmark = {
        name: name,
        filters: JSON.parse(JSON.stringify(globalFilters)),
        timestamp: new Date().toISOString()
    };

    let bookmarks = JSON.parse(localStorage.getItem('dashboard_bookmarks') || '[]');
    bookmarks.push(bookmark);
    localStorage.setItem('dashboard_bookmarks', JSON.stringify(bookmarks));

    nameInput.value = '';
    loadBookmarks();
}

function loadBookmarks() {
    const list = document.getElementById('bookmark-list');
    if (!list) return;

    let bookmarks = JSON.parse(localStorage.getItem('dashboard_bookmarks') || '[]');
    if (bookmarks.length === 0) {
        list.innerHTML = '<div class="empty-state">No saved bookmarks.</div>';
        return;
    }

    list.innerHTML = bookmarks.map((b, idx) => `
        <div class="bookmark-item">
            <span style="font-weight: 700;">${b.name}</span>
            <div class="btn-group">
                <button class="btn-accent" style="font-size: 0.65rem; padding: 2px 8px;" onclick="applyBookmark(${idx})">Load</button>
                <button class="btn-outline" style="font-size: 0.65rem; padding: 2px 8px; color: var(--error);" onclick="deleteBookmark(${idx})">Delete</button>
            </div>
        </div>
    `).join('');
}

function applyBookmark(idx) {
    let bookmarks = JSON.parse(localStorage.getItem('dashboard_bookmarks') || '[]');
    const b = bookmarks[idx];
    if (!b) return;

    globalFilters = JSON.parse(JSON.stringify(b.filters));

    // Sync UI components
    syncFactionFilters();

    // Sync turn range UI
    const minInput = document.getElementById('turn-range-min');
    const maxInput = document.getElementById('turn-range-max');
    const slider = document.getElementById('turn-range-slider');

    if (minInput) minInput.value = globalFilters.turnRange.min;
    if (maxInput) maxInput.value = globalFilters.turnRange.max;
    if (slider) slider.value = globalFilters.turnRange.max;

    // Sync metric toggles
    Object.keys(globalFilters.visibleMetrics).forEach(m => {
        const mid = `toggle-${m}`;
        const cb = document.getElementById(mid);
        if (cb) cb.checked = globalFilters.visibleMetrics[m];

        // Ensure visibility is applied correctly
        toggleMetricVisibility(m, globalFilters.visibleMetrics[m]);
    });

    refreshAllCharts();
    closeBookmarkManager();
}

function deleteBookmark(idx) {
    let bookmarks = JSON.parse(localStorage.getItem('dashboard_bookmarks') || '[]');
    bookmarks.splice(idx, 1);
    localStorage.setItem('dashboard_bookmarks', JSON.stringify(bookmarks));
    loadBookmarks();
}

function clearAllBookmarks() {
    if (confirm("Are you sure you want to clear all bookmarks?")) {
        localStorage.removeItem('dashboard_bookmarks');
        loadBookmarks();
    }
}

function exportBookmarks() {
    const data = localStorage.getItem('dashboard_bookmarks') || '[]';
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dashboard_bookmarks.json';
    a.click();
}

function importBookmarks() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = e => {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = event => {
            const bookmarks = JSON.parse(event.target.result);
            localStorage.setItem('dashboard_bookmarks', JSON.stringify(bookmarks));
            loadBookmarks();
        };
        reader.readAsText(file);
    };
    input.click();
}

// --- Persistence ---
function saveFilterState() {
    localStorage.setItem('global_filters', JSON.stringify(globalFilters));
}

function loadFilterState() {
    const saved = localStorage.getItem('global_filters');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            // Merge to handle potential new properties in future versions
            globalFilters = { ...globalFilters, ...parsed };

            // Re-apply UI state
            syncFactionFilters();

            const minInput = document.getElementById('turn-range-min');
            const maxInput = document.getElementById('turn-range-max');
            if (minInput) minInput.value = globalFilters.turnRange.min;
            if (maxInput) maxInput.value = globalFilters.turnRange.max;

            Object.keys(globalFilters.visibleMetrics).forEach(m => {
                toggleMetricVisibility(m, globalFilters.visibleMetrics[m]);
            });
        } catch (e) {
            console.error("Failed to load filter state:", e);
        }
    }
}

// --- Fleet Power & Tech Feed Extensions (Appended) ---

async function loadFleetPowerData() {
    showChartLoading('fleetPowerChart');
    try {
        const factions = globalFilters.selectedFactions.join(',');
        const { min, max } = globalFilters.turnRange;
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}&faction=${factions}&downsample=500`;

        const res = await fetchWithLogging(`/api/military/fleet_history?${query}`);
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

        const res = await fetchWithLogging(`/api/history/territory?${query}`);
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

        const res = await fetchWithLogging(`/api/history/battle_stats?${query}`);
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

// --- Initialization and Missing Functions ---

function initializeCharts() {
    if (window.chartsInitialized) return;

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { display: true, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
            y: { display: true, beginAtZero: true, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }
        },
        plugins: {
            legend: { display: true, labels: { color: '#cbd5e1' } }
        }
    };

    const createChart = (key, id, type, cfg = {}) => {
        const el = document.getElementById(id);
        if (!el) return;
        const ctx = el.getContext('2d');
        if (charts[key]) charts[key].destroy();
        charts[key] = new Chart(ctx, {
            type: type,
            data: { labels: [], datasets: [] },
            options: { ...commonOptions, ...cfg }
        });
    };

    createChart('netProfit', 'netProfitChart', 'line');
    createChart('revenueBreakdown', 'revenueBreakdownChart', 'doughnut', { scales: {} });
    createChart('stockpileVelocity', 'stockpileVelocityChart', 'bar');
    createChart('industrialDensity', 'industrialDensityChart', 'bar', { scales: { x: { stacked: true }, y: { stacked: true } } });
    createChart('queueEfficiency', 'queueEfficiencyChart', 'doughnut', { scales: {}, cutout: '70%', plugins: { legend: { display: false } } });
    createChart('techTreeProgress', 'techTreeProgressChart', 'bar', { scales: { x: { stacked: true }, y: { stacked: true } } });
    createChart('combatEffectiveness', 'combatEffectivenessChart', 'bar');
    createChart('forceComposition', 'forceCompositionChart', 'doughnut', { scales: {} });
    createChart('attritionRate', 'attritionRateChart', 'line');
    createChart('resources', 'resourceRoiChart', 'line');
    createChart('fleetPower', 'fleetPowerChart', 'line');
    createChart('territoryCount', 'territoryCountChart', 'line');
    createChart('battleStats', 'battleStatsChart', 'bar', { scales: { x: { stacked: true }, y: { stacked: true } } });

    charts.battleHeatmap = {
        canvas: document.getElementById('battleHeatmapCanvas'),
        ctx: document.getElementById('battleHeatmapCanvas')?.getContext('2d')
    };

    window.chartsInitialized = true;
    console.log("Charts Initialized");
}

async function loadIndustrialData(filter = 'all') {
    showChartLoading('industrialDensityChart');
    try {
        const query = `universe=${currentUniverse}&run_id=${currentRunId}&batch_id=${currentBatchId}`;
        const finalUrl = `/api/industrial/density?${query}&faction=${filter === 'all' ? globalFilters.selectedFactions.join(',') : filter}`;
        const res = await fetchWithLogging(finalUrl);
        const data = await res.json();
        updateIndustrialDensityChart(data, comparisonModeEnabled ? ghostData.industrial : null, filter !== 'all' ? filter : null);
        if (data.efficiency !== undefined) updateQueueEfficiencyChart(data);
    } catch (e) {
        console.error("Failed to load industrial data:", e);
    } finally {
        hideChartLoading('industrialDensityChart');
    }
}

async function loadInitialData() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('hidden');

    try {
        try {
            const [statusRes, factionsRes] = await Promise.all([
                fetchWithLogging('/api/status'),
                fetchWithLogging('/api/factions')
            ]);
            const status = await statusRes.json();
            const factions = await factionsRes.json();

            updateMetadata(status);
            initFilterControls();

            if (Array.isArray(factions) && factions.length > 0) {
                globalFilters.selectedFactions = [...factions];
                if (typeof populateFactionMultiSelect === 'function') {
                    populateFactionMultiSelect('global-faction-dropdown', factions, 'global');
                    populateFactionMultiSelect('economic-faction-dropdown', factions, 'global');
                    populateFactionMultiSelect('military-faction-dropdown', factions, 'global');
                    populateFactionMultiSelect('development-faction-dropdown', factions, 'global');
                }
                syncFactionFilters();
            }

            initializeCharts();

            await Promise.all([loadAlertData(), loadTelemetryData(), refreshAllCharts()]);

            if (typeof initGalaxyMap === 'function') initGalaxyMap();

        } catch (error) {
            console.error('Failed to load initial data:', error);
            if (typeof showUserError === 'function') showUserError("Failed to initialize dashboard", error.message);
        } finally {
            if (overlay) overlay.classList.add('hidden');
        }
    }

document.addEventListener('DOMContentLoaded', () => {
        // Debug Logger
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-log';
        debugDiv.style.cssText = "position:fixed; top:0; right:0; background:rgba(0,0,0,0.8); color:lime; padding:10px; z-index:9999; font-family:monospace; pointer-events:none; max-width:400px; max-height:100vh; overflow:auto;";
        document.body.appendChild(debugDiv);

        function log(msg) {
            console.log(msg);
            debugDiv.innerHTML += `<div>${msg}</div>`;
        }

        log("DOMContentLoaded fired.");

        try {
            log("Connecting WebSocket...");
            if (typeof connectWebSocket === 'function') {
                connectWebSocket();
                log("WebSocket connected.");
            } else {
                log("ERROR: connectWebSocket undefined");
            }
        } catch (e) { log("CRASH in connectWebSocket: " + e); }

        try {
            log("Initializing Charts...");
            if (typeof initializeCharts === 'function') {
                initializeCharts();
                log("Charts initialized.");
            } else {
                log("ERROR: initializeCharts undefined");
            }
        } catch (e) { log("CRASH in initializeCharts: " + e); }

        try {
            log("Initializing Galaxy Map...");
            if (typeof initGalaxyMap === 'function') {
                initGalaxyMap(); // Step 4
                log("Galaxy Map initialized.");
            } else {
                log("ERROR: initGalaxyMap undefined");
            }
        } catch (e) { log("CRASH in initGalaxyMap: " + e); }

        try {
            log("Loading Initial Data...");
            if (typeof loadInitialData === 'function') {
                loadInitialData().then(() => log("Initial Data Promise resolved.")).catch(e => log("Initial Data Promise REJECTED: " + e));
                log("loadInitialData called.");
            } else {
                log("ERROR: loadInitialData undefined");
            }
        } catch (e) { log("CRASH in calling loadInitialData: " + e); }

        // Resize Handler for Map
        window.addEventListener('resize', () => {
            if (window.galaxyMap && window.galaxyMap.resize) {
                window.galaxyMap.resize();
            }
        });
    });


    // --- Manual Control Features ---

    let isPaused = false;

    // Poll control status every 1s
    function startControlPolling() {
        setInterval(pollControlStatus, 1000);
        pollControlStatus(); // Initial check
    }

    async function pollControlStatus() {
        try {
            const response = await fetch('/api/control/status');
            if (!response.ok) return; // API might not be ready
            const data = await response.json();

            isPaused = data.paused;
            updateControlUI();
        } catch (e) {
            // console.debug("Control status poll failed:", e);
        }
    }

    function updateControlUI() {
        const group = document.getElementById('sim-control-group');
        const btnPause = document.getElementById('btn-play-pause');
        const btnStep = document.getElementById('btn-step');

        // Always show if API works (backend supports it)
        if (group) group.style.display = 'flex';

        if (btnPause) {
            btnPause.textContent = isPaused ? "RESUME" : "PAUSE";
            btnPause.className = isPaused ? "btn-outline" : "btn-accent";
        }

        if (btnStep) {
            btnStep.disabled = !isPaused;
            btnStep.style.opacity = isPaused ? 1 : 0.5;
        }
    }

    async function togglePause() {
        const action = isPaused ? 'resume' : 'pause';
        try {
            const response = await fetch(`/api/control/${action}`, { method: 'POST' });
            const data = await response.json();
            if (data.status === 'success') {
                isPaused = (action === 'pause');
                updateControlUI();
            }
        } catch (e) {
            console.error(`Failed to ${action}:`, e);
        }
    }

    async function triggerStep() {
        try {
            await fetch('/api/control/step', { method: 'POST' });
            // UI will update naturally via stream or next poll
        } catch (e) {
            console.error("Step trigger failed:", e);
        }
    }

