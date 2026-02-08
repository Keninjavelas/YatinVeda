"""Initialize default admin user for YatinVeda.

Run this script after database setup to create the default admin account.
Can be run multiple times safely (idempotent).

Usage:
    python scripts/init_admin.py
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from modules.bootstrap_admin import ensure_default_admin


def main():
    """Initialize the admin user."""
    print("Initializing admin user...")
    
    try:
        ensure_default_admin()
        print("✅ Admin user initialized successfully")
        print(f"   Username: Yatin")
        print(f"   Email: marcsnuffy@gmail.com")
        print(f"   Status: Active admin account ready")
    except Exception as e:
        print(f"❌ Error initializing admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
