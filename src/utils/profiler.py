import time
import functools
from src.reporting.telemetry import EventCategory

# Performance profiling decorator
def profile_method(arg=None):
    """
    Decorator to measure execution time. Can be used as @profile_method or @profile_method('metric_name').
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000.0  # ms
            
            # Determine metric name
            if isinstance(arg, str):
                metric = arg
            else:
                metric = func.__name__
                
            # Try to find telemetry/engine context
            engine = None
            if args:
                first_arg = args[0]
                # Check for engine on self (most managers)
                if hasattr(first_arg, 'engine'):
                    engine = first_arg.engine
                # Check if self IS engine (CampaignEngine)
                elif hasattr(first_arg, 'performance_metrics') and hasattr(first_arg, 'game_config'):
                    engine = first_arg
                # Check for battle context (dict)
                elif isinstance(first_arg, dict) and 'telemetry' in first_arg:
                    # Special case for tactical context dicts
                    pass
            
            # Check config if engine is available
            should_log = True
            log_level = "SUMMARY"
            if engine and hasattr(engine, 'config'):
                if hasattr(engine.config, 'performance_profile_methods'):
                     should_log = engine.config.performance_profile_methods
                if hasattr(engine.config, 'performance_logging_level'):
                     log_level = engine.config.performance_logging_level

            if should_log:
                # 1. Log to Engine Metrics (Memory)
                if engine and hasattr(engine, 'performance_metrics'):
                     if metric not in engine.performance_metrics:
                         engine.performance_metrics[metric] = []
                     engine.performance_metrics[metric].append(duration)

                # 2. Log to Telemetry (Event)
                # Resolve logger
                logger = None
                if engine and hasattr(engine, 'telemetry'):
                    logger = engine.telemetry
                elif args and isinstance(args[0], dict) and 'telemetry' in args[0]:
                    logger = args[0]['telemetry']
                elif args and hasattr(args[0], 'telemetry'): # Fallback direct attr
                    logger = args[0].telemetry

                if logger:
                    # Filter based on level (Comment 6)
                    # "detailed" or "debug" enables individual event logging?
                    # "summary" only logs aggregated summary (handled in CampaignEngine)
                    # So if level is SUMMARY, we do NOT log individual performance_metric events here.
                    if log_level.upper() in ["DETAILED", "DEBUG"]:
                        logger.log_event(EventCategory.SYSTEM, "performance_metric", {"metric": metric, "duration_ms": duration})
                
            return result
        return wrapper

    if callable(arg):
        # Called as @profile_method without args
        return decorator(arg)
    else:
        # Called as @profile_method("name")
        return decorator

def log_system_telemetry(engine):
    """
    Logs system-level telemetry:
    - Memory Usage (using psutil if available)
    - Performance Bottlenecks (from engine.performance_metrics)
    """
    if not hasattr(engine, 'telemetry') or not engine.telemetry: return

    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        # 1. Memory Usage
        if hasattr(engine.telemetry, 'log_memory_usage'):
             engine.telemetry.log_memory_usage(context={"source": "profiler"})
        else:
            engine.telemetry.log_event(
                EventCategory.SYSTEM,
                "memory_usage",
                {
                    "rss_mb": mem_info.rss / 1024 / 1024,
                    "vms_mb": mem_info.vms / 1024 / 1024,
                    "turn": engine.turn_counter
                },
                turn=engine.turn_counter
            )
    except ImportError:
        pass # psutil not installed
    except Exception as e:
        if engine.logger:
             engine.logger.error(f"Failed to log system telemetry: {e}")
    
    # 2. Performance Bottlenecks (from existing metrics)
    if hasattr(engine, 'performance_metrics'):
        bottlenecks = []
        for metric, times in engine.performance_metrics.items():
            if not times: continue
            avg_ms = sum(times) / len(times)
            if avg_ms > 100: # Threshold for bottleneck
                 bottlenecks.append({"metric": metric, "avg_ms": avg_ms, "count": len(times)})
        
        if bottlenecks:
             engine.telemetry.log_event(
                EventCategory.SYSTEM,
                "performance_bottleneck",
                {"bottlenecks": bottlenecks},
                turn=engine.turn_counter
             )
