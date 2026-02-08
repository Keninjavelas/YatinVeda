try:
    import middleware.rate_limiter
    print("Module loaded successfully")
    print("Available classes:", [x for x in dir(middleware.rate_limiter) if not x.startswith('_')])
except Exception as e:
    print(f"Error loading module: {e}")
    import traceback
    traceback.print_exc()