
try:
    import psutil
    print("PSUTIL_AVAILABLE")
except ImportError:
    print("PSUTIL_MISSING")
