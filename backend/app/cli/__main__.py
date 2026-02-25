"""Spectra CLI entry point.

Usage: python -m app.cli [command]
"""

import asyncio

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli():
    """Spectra CLI tools."""
    pass


@cli.command("seed-admin")
def seed_admin_cmd():
    """Seed or reset admin user from ADMIN_EMAIL and ADMIN_PASSWORD env vars."""
    asyncio.run(_seed_admin())


async def _seed_admin():
    """Async implementation of seed-admin command.

    Uses lazy imports inside the async function to avoid circular dependencies
    and to ensure dotenv is loaded before settings are accessed.
    """
    from app.config import get_settings
    from app.database import async_session_maker
    from app.models.api_key import ApiKey  # noqa: F401 — register model for User.api_keys relationship
    from app.services.admin.auth import seed_admin

    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        click.echo(
            "Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env", err=True
        )
        raise SystemExit(1)

    async with async_session_maker() as db:
        user = await seed_admin(
            db,
            settings.admin_email,
            settings.admin_password,
            settings.admin_first_name,
            settings.admin_last_name,
        )
        click.echo(f"Admin user '{user.email}' seeded successfully (is_admin=True)")


if __name__ == "__main__":
    cli()
