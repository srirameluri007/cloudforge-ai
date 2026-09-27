"""Seed script: idempotent demo org + admin user.

Runs only when SEED_DEMO=true or when --force is passed.
Credentials: demo@example.com / DemoPass123!
"""

from __future__ import annotations

import sys

from app.core.config import get_settings
import logging

from app.core.logging_config import configure_logging, get_logger, log_extra
from app.database.session import SessionLocal
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.services.auth_service import register_user

configure_logging("INFO")
logger = get_logger(__name__)

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPass123!"
DEMO_NAME = "Demo Admin"
DEMO_ORG_NAME = "Demo Organization"


def seed(force: bool = False) -> None:
    settings = get_settings()
    if not (settings.SEED_DEMO or force):
        logger.info("Seed skipped (SEED_DEMO is not true and --force not passed).")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing is not None:
            log_extra(
                logger,
                logging.INFO,
                "Seed skipped: demo user already exists.",
                {"email": DEMO_EMAIL},
            )
            return
        user, organization = register_user(
            db, name=DEMO_NAME, email=DEMO_EMAIL, password=DEMO_PASSWORD
        )
        # Rename the auto-created org to the canonical demo name.
        organization.name = DEMO_ORG_NAME
        membership = (
            db.query(OrganizationMembership)
            .filter(OrganizationMembership.user_id == user.id)
            .first()
        )
        if membership:
            membership.role = "admin"
        db.commit()
        log_extra(
            logger,
            logging.INFO,
            "Seeded demo organization and admin user.",
            {"org": DEMO_ORG_NAME},
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
