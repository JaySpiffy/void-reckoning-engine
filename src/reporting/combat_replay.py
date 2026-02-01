import json
import os
from typing import Dict, Any, Optional

class CombatReplayGenerator:
    """
    Transforms detailed combat logs into interactive replay data and HTML visualizations.
    """
    def __init__(self):
        self.data = None

    def load_combat_log(self, json_path: str):
        """Loads and parses the CombatTracker JSON log."""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Combat log not found: {json_path}")
            
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def generate_replay_data(self) -> Dict[str, Any]:
        """
        Transforms the flat event log into a round-by-round replay structure.
        """
        if not self.data:
            raise ValueError("No combat data loaded.")

        replay = {
            "metadata": self.data.get("meta", {}),
            "timeline": [],
            "statistics": {
                "performance": self.data.get("performance", []),
                "weapon_stats": self.data.get("meta", {}).get("weapon_statistics", {})
            }
        }

        # Group events and snapshots by round
        rounds = {}
        max_round = self.data.get("meta", {}).get("rounds", 0)

        for r in range(1, max_round + 1):
            rounds[r] = {
                "round": r,
                "events": [],
                "unit_states": []
            }

        # Process Events
        for event in self.data.get("events", []):
            r = event.get("round", 0)
            if r in rounds:
                rounds[r]["events"].append(event)

        # Process Snapshots (Reconstruct full state per round)
        for snap in self.data.get("snapshots", []):
            r = snap.get("round", 0)
            if r in rounds:
                rounds[r]["unit_states"].append(snap)

        replay["timeline"] = [rounds[r] for r in sorted(rounds.keys())]
        
        return replay

    def export_to_json(self, output_path: str):
        """Saves the processed replay data to JSON."""
        replay_data = self.generate_replay_data()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(replay_data, f, indent=2)
            
    def export_to_html(self, output_path: str):
        """
        Generates a standalone HTML file with embedded replay data and visualization player.
        """
        replay_data = self.generate_replay_data()
        json_str = json.dumps(replay_data)
        
        # We construct the HTML manually (or load a template if we had one)
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Combat Replay: {replay_data['metadata'].get('universe', 'Unknown')} Battle</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #e0e0e0; margin: 0; display: flex; height: 100vh; }}
        #sidebar {{ width: 300px; background: #252525; padding: 20px; overflow-y: auto; border-right: 1px solid #333; }}
        #main {{ flex: 1; display: flex; flex-direction: column; }}
        #grid-container {{ flex: 1; position: relative; background: #000; overflow: hidden; display: flex; justify-content: center; align-items: center; }}
        canvas#tactical-grid {{ background: #050505; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
        #controls {{ height: 60px; background: #2d2d2d; display: flex; align-items: center; padding: 0 20px; gap: 10px; border-top: 1px solid #333; }}
        input[type="range"] {{ flex: 1; }}
        .btn {{ background: #3c3c3c; border: none; color: white; padding: 8px 16px; cursor: pointer; border-radius: 4px; }}
        .btn:hover {{ background: #4a4a4a; }}
        .header {{ font-size: 1.2em; margin-bottom: 15px; color: #4fc3f7; border-bottom: 1px solid #444; padding-bottom: 5px; }}
        .event-log {{ font-size: 0.9em; max-height: 200px; overflow-y: auto; font-family: monospace; }}
        .event-item {{ margin-bottom: 4px; padding: 4px; border-radius: 2px; }}
        .event-weapon {{ color: #ff8a80; }}
        .event-kill {{ color: #ff5252; font-weight: bold; }}
        .event-ability {{ color: #b388ff; }}
        .stat-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="header">Battle Info</div>
        <div class="stat-row"><span>Winner:</span> <span style="color: #4caf50">{replay_data['metadata'].get('winner')}</span></div>
        <div class="stat-row"><span>Rounds:</span> <span>{replay_data['metadata'].get('rounds')}</span></div>
        <div class="stat-row"><span>Timestamp:</span> <span>{replay_data['metadata'].get('timestamp')}</span></div>
        
        <br>
        <div class="header">Selected Unit</div>
        <div id="unit-info">Click a unit to see details</div>
        
        <br>
        <div class="header">Event Log</div>
        <div id="round-events" class="event-log"></div>
    </div>
    
    <div id="main">
        <div id="grid-container">
            <canvas id="tactical-grid" width="800" height="800"></canvas>
        </div>
        <div id="controls">
            <button class="btn" onclick="togglePlay()" id="play-btn">Play</button>
            <button class="btn" onclick="step(-1)">Prev</button>
            <span id="round-display">Round 0</span>
            <input type="range" id="timeline-scrubber" min="0" max="{len(replay_data['timeline'])}" value="0" step="1" oninput="scrub(this.value)">
            <button class="btn" onclick="step(1)">Next</button>
            <select id="speed-select" onchange="setSpeed(this.value)" class="btn">
                <option value="1000">1x</option>
                <option value="500">2x</option>
                <option value="200">5x</option>
                <option value="100">10x</option>
            </select>
        </div>
    </div>

    <script>
        const replayData = {json_str};
        const canvas = document.getElementById('tactical-grid');
        const ctx = canvas.getContext('2d');
        const gridSize = 100;
        const cellSize = canvas.width / gridSize;
        
        let currentRoundIdx = 0;
        let isPlaying = false;
        let playInterval = null;
        let playSpeed = 1000;
        let selectedUnit = null;
        
        function init() {{
            drawGrid();
            renderFrame(0);
        }}
        
        function drawGrid() {{
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 1;
            for(let i=0; i<=gridSize; i++) {{
                ctx.beginPath();
                ctx.moveTo(i*cellSize, 0);
                ctx.lineTo(i*cellSize, canvas.height);
                ctx.stroke();
                
                ctx.beginPath();
                ctx.moveTo(0, i*cellSize);
                ctx.lineTo(canvas.width, i*cellSize);
                ctx.stroke();
            }}
        }}
        
        function renderFrame(roundIdx) {{
            if (roundIdx < 0 || roundIdx >= replayData.timeline.length) return;
            
            // Clear but keep grid background or redraw
            ctx.fillStyle = '#050505';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            drawGrid();
            
            const roundData = replayData.timeline[roundIdx];
            document.getElementById('round-display').innerText = "Round " + roundData.round;
            document.getElementById('timeline-scrubber').value = roundIdx;
            
            // Render Units
            roundData.unit_states.forEach(u => {{
                if (!u.is_alive && roundIdx > 0) return; // Hide dead units unless just died?
                // Or maybe show debris?
                
                const x = u.position.x * cellSize;
                const y = u.position.y * cellSize;
                
                ctx.fillStyle = getFactionColor(u.faction);
                ctx.beginPath();
                ctx.arc(x + cellSize/2, y + cellSize/2, cellSize * 0.8, 0, Math.PI * 2);
                ctx.fill();
                
                // Direction indicator
                if (u.position.facing !== undefined) {{
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(x + cellSize/2, y + cellSize/2);
                    // Convert facing (0=North, 90=East) to radians. Correct for canvas coords (y down)
                    // Canvas Angle: 0 = Right (East). 
                    // Facing 0 (North) -> -PI/2
                    const angle = (u.position.facing - 90) * (Math.PI/180);
                    ctx.lineTo(x + cellSize/2 + Math.cos(angle)*cellSize, y + cellSize/2 + Math.sin(angle)*cellSize);
                    ctx.stroke();
                }}
                
                // HP Bar
                const hpPct = u.hp / u.max_hp;
                ctx.fillStyle = 'red';
                ctx.fillRect(x, y - 4, cellSize, 2);
                ctx.fillStyle = 'green';
                ctx.fillRect(x, y - 4, cellSize * hpPct, 2);
            }});
            
            // Visualize Events (Transient)
            // This is tricky for a static frame render, but we can draw lines for shooting events in this round
            roundData.events.forEach(e => {{
                if (e.type === 'weapon_fire_detailed' || e.type === 'weapon_fire') {{
                    const attacker = findUnitPos(roundData.unit_states, e.attacker);
                    const target = findUnitPos(roundData.unit_states, e.target);
                    
                    if (attacker && target) {{
                        ctx.strokeStyle = e.hit_result ? 'rgba(255, 100, 100, 0.5)' : 'rgba(255, 255, 255, 0.1)';
                        ctx.lineWidth = e.hit_result ? 2 : 1;
                        ctx.beginPath();
                        ctx.moveTo(attacker.x * cellSize + cellSize/2, attacker.y * cellSize + cellSize/2);
                        ctx.lineTo(target.x * cellSize + cellSize/2, target.y * cellSize + cellSize/2);
                        ctx.stroke();
                        
                        if (e.hit_result) {{
                            // Impact burst
                            ctx.fillStyle = 'orange';
                            ctx.beginPath();
                            ctx.arc(target.x * cellSize + cellSize/2, target.y * cellSize + cellSize/2, cellSize/2, 0, Math.PI * 2);
                            ctx.fill();
                        }}
                    }}
                }}
            }});
            
            updateLog(roundData.events);
        }}
        
        function getFactionColor(faction) {{
            // Simple hash to color
            let hash = 0;
            for (let i = 0; i < faction.length; i++) {{
                hash = faction.charCodeAt(i) + ((hash << 5) - hash);
            }}
            const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
            return '#' + "00000".substring(0, 6 - c.length) + c;
        }}
        
        function findUnitPos(units, name) {{
            const unit = units.find(u => u.unit === name);
            return unit ? unit.position : null;
        }}
        
        function updateLog(events) {{
            const log = document.getElementById('round-events');
            log.innerHTML = '';
            events.forEach(e => {{
                const div = document.createElement('div');
                div.className = 'event-item';
                let text = `[${{e.timestamp.split('T')[1].split('.')[0]}}] `;
                
                if (e.type === 'weapon_fire_detailed') {{
                    div.classList.add('event-weapon');
                    text += `${{e.attacker}} fired ${{e.weapon}} at ${{e.target}}. Result: ${{e.hit_result ? 'HIT' : 'MISS'}}`;
                    if (e.killed) {{
                        text += ' (KILL)';
                        div.classList.add('event-kill');
                    }}
                }} else if (e.type === 'ability_activation') {{
                    div.classList.add('event-ability');
                    text += `${{e.attacker}} used ${{e.ability_name}} on ${{e.target}}. ${{e.description}}`;
                }} else {{
                    text += `${{e.type}}: ${{e.attacker}} -> ${{e.target}}`;
                }}
                div.innerText = text;
                log.appendChild(div);
            }});
        }}
        
        function step(delta) {{
            const newIdx = currentRoundIdx + delta;
            if (newIdx >= 0 && newIdx < replayData.timeline.length) {{
                currentRoundIdx = newIdx;
                renderFrame(currentRoundIdx);
            }}
        }}
        
        function scrub(val) {{
            currentRoundIdx = parseInt(val);
            renderFrame(currentRoundIdx);
        }}
        
        function togglePlay() {{
            isPlaying = !isPlaying;
            document.getElementById('play-btn').innerText = isPlaying ? "Pause" : "Play";
            if (isPlaying) {{
                playInterval = setInterval(() => step(1), playSpeed);
            }} else {{
                clearInterval(playInterval);
            }}
        }}

        function setSpeed(val) {{
            playSpeed = parseInt(val);
            if (isPlaying) {{
                clearInterval(playInterval);
                playInterval = setInterval(() => step(1), playSpeed);
            }}
        }}
        
        init();
    </script>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

if __name__ == "__main__":
    # Test stub
    pass
