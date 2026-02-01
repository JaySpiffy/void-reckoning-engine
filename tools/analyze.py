import sys
import subprocess
import os

def print_help():
    print("Unified Log Analysis Tool")
    print("Usage: python tools/analyze.py <command> [args]")
    print("\nCommands:")
    print("  query       : Run structured or natural language queries")
    print("  patterns    : Mine frequent event patterns (LogAnalyzer)")
    print("  errors      : Analyze error distribution (LogAnalyzer)")
    print("  performance : Profile simulation performance (LogAnalyzer)")
    print("  correlation : Analyze metric correlations (LogAnalyzer)")
    print("  diff        : Compare two runs (LogDiffer)")
    print("\nExamples:")
    print("  analyze.py query \"battles where Imperium won\"")
    print("  analyze.py patterns --universe warhammer40k")
    print("  analyze.py diff run_001 run_002 --mode stats")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    
    base_dir = os.path.dirname(__file__) # tools/
    
    # Map commands to scripts
    # scripts are in tools/ or tools/analysis/
    
    scripts = {
        "query": os.path.join(base_dir, "report_query.py"),
        "patterns": os.path.join(base_dir, "analysis", "log_analyzer.py"),
        "errors": os.path.join(base_dir, "analysis", "log_analyzer.py"),
        "performance": os.path.join(base_dir, "analysis", "log_analyzer.py"),
        "correlation": os.path.join(base_dir, "analysis", "log_analyzer.py"),
        "diff": os.path.join(base_dir, "analysis", "log_diff.py")
    }
    
    if command not in scripts:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)
        
    script_path = scripts[command]
    
    # Construct subprocess command
    cmd = [sys.executable, script_path]
    
    # Analyze commands need to pass the subcommand to log_analyzer.py
    if command in ["patterns", "errors", "performance", "correlation"]:
        # log_analyzer expects: python log_analyzer.py [mode] [args]
        # map 'patterns' -> 'pattern' (singular expected by log_analyzer arg parser)
        # map 'performance' -> 'performance'
        mode_map = {
            "patterns": "pattern",
            "errors": "errors",
            "performance": "performance", 
            "correlation": "correlation"
        }
        cmd.append(mode_map[command])
        cmd.extend(args)
    elif command == "query":
        # report_query.py expects args. If first arg is natural language without flag?
        # The parser for report_query.py has --query-nl.
        # If user typed: analyze.py query "some text"
        # We need to detect if "some text" is a flag or bare text.
        # If bare string, assume --query-nl.
        if args and not args[0].startswith("-"):
            # Assume it's a natural language query
            cmd.extend(["--query-nl", args[0]])
            cmd.extend(args[1:])
        else:
            cmd.extend(args)
    else:
        # Diff
        cmd.extend(args)
        
    # Execute
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except Exception as e:
        print(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
