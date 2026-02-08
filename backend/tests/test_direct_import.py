import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.getcwd())

try:
    # Try to import the module directly
    import middleware.rate_limiter as rl
    print("Module imported successfully")
    
    # Check what's in the module
    print("Module attributes:", [x for x in dir(rl) if not x.startswith('_')])
    
    # Try to access specific classes
    try:
        print("AdvancedRateLimiter:", rl.AdvancedRateLimiter)
    except AttributeError as e:
        print("AdvancedRateLimiter not found:", e)
    
    try:
        print("RateLimitAction:", rl.RateLimitAction)
    except AttributeError as e:
        print("RateLimitAction not found:", e)
        
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()