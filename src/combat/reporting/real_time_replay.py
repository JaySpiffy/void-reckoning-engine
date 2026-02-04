import json
import os
from typing import Dict, List, Any
from datetime import datetime

class RealTimeReplayGenerator:
    """
    Generates high-fidelity Post-Action Reports (PAR) for real-time combat headless runs.
    """
    def __init__(self, combat_state: Any, winner_override: str = None):
        self.state = combat_state
        self.winner_override = winner_override
        self.snapshots = getattr(combat_state, 'snapshots', [])
        self.event_log = getattr(combat_state, 'event_log', [])
        
        # [VERIFICATION FIX] Merge events from CombatTracker if available
        if hasattr(combat_state, 'tracker') and combat_state.tracker:
             tracker_events = getattr(combat_state.tracker, 'events', [])
             # We extend the list. Note: Timestamps might differ (float vs ISO), 
             # but for verification scanning, presence is enough.
             self.event_log.extend(tracker_events)
             
        self.total_time = getattr(combat_state, 'total_sim_time', 0.0)

    def generate_par(self) -> Dict[str, Any]:
        """Calculates Post-Action Report statistics."""
        winner = self.winner_override
        if not winner:
            winner = self.state.active_factions[0] if len(self.state.active_factions) == 1 else "Draw"
            
        par = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "duration": round(self.total_time, 2),
                "map": self.state.grid.name if hasattr(self.state.grid, 'name') else "Tactical Grid",
                "winner": winner
            },
            "factions": {},
            "objective_timeline": [],
            "formation_stats": {}
        }

        # Initialize faction stats
        for f_name in self.state.armies_dict.keys():
            par["factions"][f_name] = {
                "initial_strength": len(self.state.armies_dict[f_name]),
                "survivors": sum(1 for u in self.state.armies_dict[f_name] if u.is_alive()),
                "vp": round(self.state.victory_points.get(f_name, 0.0), 1),
                "damage_dealt": 0
            }

        # Calculate damage from event log
        for event in self.event_log:
            if event["type"] == "shooting":
                attacker_faction = self._get_faction_by_unit_name(event["attacker"])
                if attacker_faction:
                    desc = event["description"]
                    # Format: "Shot hit for X DMG" or "Shot hit for X DMG [SIDE]"
                    try:
                        # Extract number between "for " and " DMG"
                        if "for " in desc and " DMG" in desc:
                            start = desc.find("for ") + 4
                            end = desc.find(" DMG")
                            dmg_val = int(desc[start:end])
                            par["factions"][attacker_faction]["damage_dealt"] += dmg_val
                    except ValueError:
                        pass

        # Summary of objective control (Approximate from events)
        capture_events = [e for e in self.event_log if e["type"] == "capture"]
        for e in capture_events:
            par["objective_timeline"].append({
                "time": round(e["timestamp"], 1),
                "objective": e["target"],
                "new_owner": e["attacker"]
            })

        return par

    def _get_faction_by_unit_name(self, name: str) -> str:
        for f_name, units in self.state.armies_dict.items():
            if any(u.name == name for u in units):
                return f_name
        return "Unknown"

    def export_json(self, path: str):
        """Saves a full 'Black Box' report for analysis or visualizers."""
        report = {
            "par": self.generate_par(),
            "events": self.event_log,
            "snapshots": self.snapshots
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    def export_html_summary(self, path: str):
        """Creates a readable HTML summary with a 'filmstrip' view."""
        par = self.generate_par()
        
        # Simple HTML template for PAR
        html = f"""
        <html>
        <head>
            <title>PAR: {par['meta']['map']}</title>
            <style>
                body {{ font-family: sans-serif; background: #121212; color: #eee; padding: 20px; }}
                .stat-box {{ background: #1e1e1e; border: 1px solid #333; padding: 15px; margin-bottom: 20px; border-radius: 8px; }}
                h1, h2 {{ color: #4fc3f7; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
                .winner {{ color: #4caf50; font-weight: bold; }}
                .event-log {{ font-family: monospace; font-size: 0.9em; height: 300px; overflow-y: auto; background: #000; padding: 10px; }}
            </style>
        </head>
        <body>
            <h1>Post-Action Report: {par['meta']['map']}</h1>
            <div class="stat-box">
                <p><strong>Winner:</strong> <span class="winner">{par['meta']['winner']}</span></p>
                <p><strong>Duration:</strong> {par['meta']['duration']}s</p>
            </div>
            
            <h2>Faction Performance</h2>
            <table>
                <tr>
                    <th>Faction</th>
                    <th>Init Strength</th>
                    <th>Survivors</th>
                    <th>Damage Dealt</th>
                    <th>VP</th>
                </tr>
        """
        for f, stats in par["factions"].items():
            html += f"""
                <tr>
                    <td>{f}</td>
                    <td>{stats['initial_strength']}</td>
                    <td>{stats['survivors']}</td>
                    <td>{stats['damage_dealt']}</td>
                    <td>{stats['vp']}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Objective Capture History</h2>
            <table>
                <tr><th>Time</th><th>Objective</th><th>New Owner</th></tr>
        """
        for e in par["objective_timeline"]:
            html += f"<tr><td>{e['time']}s</td><td>{e['objective']}</td><td>{e['new_owner']}</td></tr>"
            
        html += """
            </table>
            
            <h2>Battle Log (Highlights)</h2>
            <div class="event-log">
        """
        # Only log 50 most interesting events for summary
        highlights = [e for e in self.event_log if e["type"] in ["capture", "morale", "flank"]]
        for e in highlights[-50:]:
             html += f"<div>[{round(e['timestamp'], 1)}s] <b>{e['type'].upper()}</b>: {e['attacker']} @ {e['target']} - {e['description']}</div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    def export_text_log(self, path: str):
        """Generates a human-readable text log of the battle."""
        par = self.generate_par()
        
        lines = []
        lines.append(f"=== BATTLE LOG: {par['meta']['map']} ===")
        lines.append(f"Winner: {par['meta']['winner']}")
        lines.append(f"Duration: {par['meta']['duration']}s")
        lines.append(f"Timestamp: {par['meta']['timestamp']}")
        lines.append("-" * 40)
        
        lines.append("\n[FACTION PERFORMANCE]")
        for f, stats in par["factions"].items():
            lines.append(f"Faction: {f}")
            lines.append(f"  Initial Strength: {stats['initial_strength']}")
            lines.append(f"  Survivors:        {stats['survivors']}")
            lines.append(f"  Damage Dealt:     {stats['damage_dealt']}")
            lines.append(f"  Victory Points:   {stats['vp']}")
            lines.append("")
            
        lines.append("-" * 40)
        lines.append("\n[OBJECTIVE HISTORY]")
        for e in par["objective_timeline"]:
            lines.append(f"T+{e['time']}s: {e['objective']} captured by {e['new_owner']}")
            
        lines.append("-" * 40)
        lines.append("\n[COMBAT NARRATIVE]")
        for e in self.event_log:
            ts_val = e.get('timestamp', 0)
            try:
                ts = round(float(ts_val), 1)
            except (ValueError, TypeError):
                ts = 0.0
            etype = e.get('type', 'UNKNOWN').upper()
            attacker = e.get('attacker', 'Unknown')
            target = e.get('target', 'Unknown')
            desc = e.get('description', '')
            
            # [CINEMATIC ENHANCEMENTS] 
            # Translate technical events into game-like narrative
            if etype == "MORALE_FAILURE":
                 lines.append(f"[{ts:6.1f}s] [SHATTERED] {attacker}'s resolve breaks! The unit is in full retreat!")
            elif etype == "CHAIN_ROUTING":
                 lines.append(f"[{ts:6.1f}s] [PANIC] Nearby routing allies have broken the morale of {attacker}!")
            elif etype == "HARDPOINT_DESTROYED":
                 lines.append(f"[{ts:6.1f}s] [CRITICAL] {attacker} scores a direct hit on {target}'s {desc}! The hardpoint is OBLITERATED!")
            elif etype == "CAPTURE":
                 lines.append(f"[{ts:6.1f}s] [CAPTURE] {attacker} has SEIZED control of {target}! Prize crew established.")
            elif etype == "BOARDING" and "Captured" in desc:
                 lines.append(f"[{ts:6.1f}s] [INVASION] {attacker} boarding parties have seized control of {target}! The ship is lost!")
            else:
                 lines.append(f"[{ts:6.1f}s] {etype:<10} {attacker} -> {target}: {desc}")
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
