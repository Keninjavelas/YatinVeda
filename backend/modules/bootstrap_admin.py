"""Bootstrap a default admin user for YatinVeda.

This creates (if missing) an admin user with:
- username: Yatin
- email:   marcsnuffy@gmail.com
- password: LeoPolly

These values are hard-coded per project requirements. Treat this
project as private, since hard-coding credentials is not suitable for
public/production use.
"""

from __future__ import annotations

from typing import Optional

from database import SessionLocal
from models.database import User
from modules.auth import get_password_hash


ADMIN_USERNAME = "Yatin"
ADMIN_EMAIL = "marcsnuffy@gmail.com"
ADMIN_PASSWORD_PLAIN = "LeoPolly"


def ensure_default_admin() -> None:
    """Ensure the default admin user exists in the primary database.

    Idempotent: if a user with the admin username or email already
    exists, it will not create another one. If found but not marked as
    admin, it upgrades that user to admin.
    """
    db = SessionLocal()
    try:
        user: Optional[User] = (
            db.query(User)
            .filter((User.username == ADMIN_USERNAME) | (User.email == ADMIN_EMAIL))
            .first()
        )

        if user is None:
            user = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD_PLAIN),
                full_name=ADMIN_USERNAME,
                is_active=True,
                is_admin=True,
            )
            db.add(user)
            db.commit()
        else:
            changed = False
            if not user.is_admin:
                user.is_admin = True
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                db.commit()
    finally:
        db.close()
