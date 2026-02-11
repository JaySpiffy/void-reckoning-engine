import sys
import io
import subprocess
# Force UTF-8 for Windows Consoles
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.cli.main import main

def show_interactive_menu():
    print("\n=== Multi-Universe Campaign Simulator ===")
    print("1. Quick Campaign (30 turns)")
    print("2. Batch Campaign (100 runs)")
    print("3. Multi-Universe Parallel Simulation")
    print("4. Tactical Combat")
    print("5. Data Validation")
    print("6. Select Active Universe")
    print("7. Cross-Universe Duel (1v1)")
    print("8. Multi-Universe Fleet Battle (Mixed)")
    print("9. Launch Terminal Dashboard (Demo)")
    print("10. Custom Report Export")
    print("0. Exit")
    
    choice = input("\nSelect an option: ")
    
    if choice == "1":
        universe = get_active_universe_interactive()
        sys.argv = ["campaign_sim", "campaign", "--quick", "--universe", universe]
        main()
    elif choice == "2":
        universe = get_active_universe_interactive()
        sys.argv = ["campaign_sim", "campaign", "--batch", "--universe", universe]
        main()
    elif choice == "3":
        # ... (Existing Multi-Universe Logic)
        print("\nMulti-Universe Configuration:")
        print("1. Use existing config file")
        print("2. Auto-select universes to run")
        mu_choice = input("Select option (default 1): ").strip()
        
        if mu_choice == "2":
            from src.core.config import list_available_universes
            import json
            import os
            
            avail = list_available_universes()
            print("\nAvailable Universes:")
            for i, u in enumerate(avail, 1):
                print(f"{i}. {u}")
                
            selection = input("\nEnter universe numbers to run (comma separated, e.g. '1,3'): ").strip()
            if not selection:
                print("No selection made. Aborting.")
                show_interactive_menu()
                return

            try:
                indices = [int(s.strip()) - 1 for s in selection.split(",")]
                selected_unis = [avail[i] for i in indices if 0 <= i < len(avail)]
            except ValueError:
                print("Invalid input.")
                show_interactive_menu()
                return

            if not selected_unis:
                print("No valid universes selected.")
                show_interactive_menu()
                return

            print(f"Selected: {', '.join(selected_unis)}")
            
            # Generate temporary config
            base_config = {
                "mode": "multi",
                "universes": [],
                "multi_universe_settings": {
                    "sync_turns": False,
                    "cross_universe_events": False, 
                    "aggregate_reports": True
                },
                "simulation": { 
                    "max_workers": 12, 
                    "output_dir": "reports" 
                }
            }
            
            # Assign CPU affinity (simple round-robin or chunking)
            total_cores = os.cpu_count() or 4
            cores_per_uni = max(1, total_cores // len(selected_unis))
            
            current_core = 0
            for uname in selected_unis:
                affinity = list(range(current_core, min(current_core + cores_per_uni, total_cores)))
                current_core += cores_per_uni
                
                # Basic default settings for any universe
                u_conf = {
                    "name": uname,
                    "enabled": True,
                    "processor_affinity": affinity,
                    "num_runs": 10,
                    "campaign": { "turns": 100, "num_systems": 10, "min_planets": 5, "max_planets": 10, "combat_rounds": 100 },
                    "economy": { "base_income_req": 10000, "base_income_prom": 1000, "colonization_cost": 5000 },
                    "units": { "max_fleet_size": 20, "max_land_army_size": 20 },
                    "mechanics": { "enable_diplomacy": True, "enable_weather": False },
                    "reporting": { "formats": ["json"] }
                }
                base_config["universes"].append(u_conf)
                
            temp_config_path = "temp_multi_config.json"
            with open(temp_config_path, "w") as f:
                json.dump(base_config, f, indent=4)
                
            print(f"\nGenerated temporary config: {temp_config_path}")
            sys.argv = ["campaign_sim", "multi-universe", "--config", temp_config_path]
            main()
            
            # Clean up handled by OS or next run overwrite, 
            # or we could try/finally logic in main, but run.py hands off control.
            
        else:
            config_path = input("Path to multi-universe config (default: config/unified_simulation_config.json): ").strip()
            if not config_path:
                config_path = "config/unified_simulation_config.json"
            
            # Offer to filter
            import json
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    defined_unis = [u["name"] for u in data.get("universes", [])]
                
                if defined_unis:
                    print(f"\nUniverses defined in {config_path}:")
                    for i, u in enumerate(defined_unis, 1):
                        print(f"{i}. {u}")
                    
                    filter_choice = input("\nRun specific universes? (Enter numbers comma-separated, or Enter for all): ").strip()
                    if filter_choice:
                        try:
                            indices = [int(s.strip()) - 1 for s in filter_choice.split(",")]
                            selected = [defined_unis[i] for i in indices if 0 <= i < len(defined_unis)]
                            if selected:
                                sys.argv = ["campaign_sim", "multi-universe", "--config", config_path, "--universes", ",".join(selected)]
                                main()
                                return
                        except ValueError:
                            print("Invalid selection, running all.")
            except Exception as e:
                print(f"Warning: Could not read config for filtering: {e}")
            
            # PHASE 22: AUTO VALIDATION
            from src.utils.setup_validator import run_validations
            if not run_validations(config_path):
                print("\n[ERROR] Setup Validation Failed. Please fix the issues above before running.")
                input("Press Enter to return to menu...")
                show_interactive_menu()
                return

            sys.argv = ["campaign_sim", "multi-universe", "--config", config_path]
            main()
    elif choice == "4":
        universe = get_active_universe_interactive()
        print("\nCombat Modes:")
        print("1. Duel")
        print("2. Grand Royale")
        print("3. Fleet Battle")
        sub_choice = input("Select combat mode: ")
        if sub_choice == "1":
            u1 = input("Unit 1: ")
            u2 = input("Unit 2: ")
            sys.argv = ["campaign_sim", "simulate", "--mode", "duel", "--units", u1, u2, "--universe", universe]
            main()
        elif sub_choice == "2":
            sys.argv = ["campaign_sim", "simulate", "--mode", "royale", "--universe", universe]
            main()
        elif sub_choice == "3":
            f1 = input("Faction 1: ")
            f2 = input("Faction 2: ")
            sys.argv = ["campaign_sim", "simulate", "--mode", "fleet", "--faction1", f1, "--faction2", f2, "--universe", universe]
            main()
    elif choice == "7":
        print("\nCross-Universe Duel:")
        print("Format: universe:faction:unit_name")
        u1 = input("Unit 1: ")
        u2 = input("Unit 2: ")
        battle_uni = input("Battle Universe (default: auto): ").strip()
        sys.argv = ["campaign_sim", "cross-universe-duel", "--unit1", u1, "--unit2", u2]
        if battle_uni:
            sys.argv.extend(["--battle-universe", battle_uni])
        main()
    elif choice == "8":
        print("\nMulti-Universe Fleet Battle:")
        f1 = input("Faction 1: ")
        f2 = input("Faction 2: ")
        u_context = input("Battle Universe Context (e.g. warhammer40k): ")
        sys.argv = ["campaign_sim", "simulate", "--mode", "fleet", "--faction1", f1, "--faction2", f2, "--multi-universe", "--universe", u_context]
        main()
    elif choice == "5":
        universe = get_active_universe_interactive()
        validate_universe(universe) # Step 15
        sys.argv = ["campaign_sim", "validate", "--rebuild-registries", "--universe", universe]
        main()

    elif choice == "6":
        select_universe_interactive()
        show_interactive_menu()
    elif choice == "9":
        universe = get_active_universe_interactive()
        # Launch using the new dashboard CLI command (interactive)
        sys.argv = ["campaign_sim", "dashboard", "--universe", universe]
        main()
    elif choice == "10":
        universe = get_active_universe_interactive()
        print("\nExport Options:")
        print("1. Analytics Report (Campaign Scope)")
        print("2. Specific Run Report")
        print("3. Batch Summary")
        print("4. Cross-Universe Comparison")
        
        ex_choice = input("Select scope: ").strip()
        
        print("\nAvailable Formats: json, markdown, html, csv, excel, pdf")
        print("Enter formats separated by space (e.g. 'pdf excel'). Default: 'pdf excel'")
        fmt_input = input("Formats: ").strip()
        formats = fmt_input.split() if fmt_input else ["pdf", "excel"]
        
        output_dir = input("Output directory (default: reports/exports): ").strip() or "reports/exports"
        webhook = input("Webhook URL (optional, press Enter to skip): ").strip()
        
        if ex_choice == "1":
            # Analytics (Campaign Scope)
            sys.argv = ["campaign_sim", "export", "analytics", "--universe", universe, "--output-dir", output_dir, "--formats"] + formats
            if webhook:
                sys.argv.extend(["--webhook", webhook])
            main()
            
        elif ex_choice == "2":
            # Specific Run
            run_id = input("Run ID: ").strip()
            if not run_id:
                print("Run ID required.")
                show_interactive_menu()
                return
            
            cmd = ["campaign_sim", "export", "report", "--universe", universe, "--run-id", run_id, "--output-dir", output_dir, "--formats"] + formats
            if webhook:
                 cmd.extend(["--webhook", webhook])
            sys.argv = cmd
            main()

        elif ex_choice == "3":
             # Batch Summary (Analytics)
             sys.argv = ["campaign_sim", "export", "analytics", "--universe", universe, "--output-dir", output_dir, "--formats"] + formats
             if webhook:
                 sys.argv.extend(["--webhook", webhook])
             main()


    elif choice == "0":
        sys.exit(0)
    else:
        print("Invalid choice.")
        show_interactive_menu()

def validate_universe(universe):
    """Checks for invalid doctrine tags in faction personalities."""
    print(f"\nValidating Tech Doctrines for {universe}...")
    errors = []
    try:
        import importlib
        mod_path = f"universes.{universe}.ai_personalities"
        ai_pers = importlib.import_module(mod_path)
        
        if hasattr(ai_pers, 'PERSONALITY_DB'):
            valid_doctrines = ["RADICAL", "PURITAN", "PRAGMATIC", "XENOPHOBIC", "ADAPTIVE"]
            for f_name, pers in ai_pers.PERSONALITY_DB.items():
                if hasattr(pers, 'tech_doctrine'):
                    if pers.tech_doctrine not in valid_doctrines:
                        errors.append(f"Invalid tech_doctrine '{pers.tech_doctrine}' for {f_name}")
    except Exception as e:
        pass
    
    if errors:
        print("  [FAILED] Doctrine Validation Errors:")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  [SUCCESS] All faction doctrines valid.")
    return len(errors) == 0

def get_active_universe_interactive():
    """Get the currently active universe or prompt user to select one."""
    from src.core.config import get_active_universe, list_available_universes
    
    current = get_active_universe()
    if not current:
         return select_universe_interactive()

    available = list_available_universes()
    
    print(f"\nCurrent universe: {current}")
    # print("Available universes:", ", ".join(available))
    
    use_current = input(f"Use '{current}'? (y/n): ").strip().lower()
    if use_current == 'y' or use_current == '':
        return current
    
    return select_universe_interactive()

def select_universe_interactive():
    """Interactive universe selection."""
    from src.core.config import list_available_universes, set_active_universe
    
    available = list_available_universes()
    
    print("\nAvailable Universes:")
    for i, uni in enumerate(available, 1):
        print(f"{i}. {uni}")
    
    choice = input("\nSelect universe number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(available):
            selected = available[idx]
            set_active_universe(selected)
            print(f"Active universe set to: {selected}")
            return selected
        else:
            print("Invalid selection.")
            return select_universe_interactive()
    except ValueError:
        print("Invalid input.")
        return select_universe_interactive()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        show_interactive_menu()
