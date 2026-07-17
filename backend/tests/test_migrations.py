import os
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.migration


BACKEND_DIRECTORY = (
    Path(__file__).resolve().parent.parent
)


def run_alembic_command(
    database_url: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """
    Run Alembic against an isolated test database.
    """

    environment = os.environ.copy()

    environment["DATABASE_URL"] = database_url

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            *arguments,
        ],
        cwd=BACKEND_DIRECTORY,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_migrations_upgrade_and_downgrade(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "migration_test.db"
    )

    database_url = (
        "sqlite:///"
        f"{database_path.as_posix()}"
    )

    upgrade_result = run_alembic_command(
        database_url,
        "upgrade",
        "head",
    )

    assert (
        upgrade_result.returncode
        == 0
    ), (
        upgrade_result.stdout
        + upgrade_result.stderr
    )

    assert database_path.exists()

    current_result = run_alembic_command(
        database_url,
        "current",
    )

    assert (
        current_result.returncode
        == 0
    ), (
        current_result.stdout
        + current_result.stderr
    )

    current_output = (
        current_result.stdout
        + current_result.stderr
    )

    assert "(head)" in current_output

    downgrade_result = run_alembic_command(
        database_url,
        "downgrade",
        "base",
    )

    assert (
        downgrade_result.returncode
        == 0
    ), (
        downgrade_result.stdout
        + downgrade_result.stderr
    )

    second_upgrade_result = (
        run_alembic_command(
            database_url,
            "upgrade",
            "head",
        )
    )

    assert (
        second_upgrade_result.returncode
        == 0
    ), (
        second_upgrade_result.stdout
        + second_upgrade_result.stderr
    )