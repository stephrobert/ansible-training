"""Plugin pytest qui inscrit chaque run dans la SQLite locale.

Activé via conftest.py : `pytest_plugins = ["dsoxlab.pytest_plugin"]`.

Détecte automatiquement le `lab_path` (`<section>/<lab>`) à partir du chemin
des fichiers de test collectés, démarre un run au début de la session,
inscrit chaque test, finalise à la fin.

Désactivable via env `DSOXLAB_DISABLED=1` (utile en CI).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from . import db, meta


def _is_disabled() -> bool:
    return os.environ.get("DSOXLAB_DISABLED") == "1"


def _detect_lab_path(items) -> str | None:
    """Détecte le `<section>/<lab>` commun à tous les items collectés.

    Retourne None si :
    - aucun item n'est dans labs/<sect>/<lab>/...
    - les items sont dans plusieurs labs différents (run cross-lab, on n'inscrit pas)
    """
    try:
        repo_root = meta.find_repo_root()
    except FileNotFoundError:
        return None

    labs_dir = repo_root / "labs"
    detected: set[str] = set()

    for item in items:
        path = Path(item.fspath).resolve()
        try:
            rel = path.relative_to(labs_dir)
        except ValueError:
            continue
        # rel = "vault/introduction/challenge/tests/test_xxx.py"
        if len(rel.parts) >= 2:
            detected.add(f"{rel.parts[0]}/{rel.parts[1]}")

    if len(detected) == 1:
        return detected.pop()
    return None


def pytest_configure(config):
    """Stocke un emplacement pour le run_id sur la session."""
    config._dsoxlab_run_id = None
    config._dsoxlab_lab_path = None


def pytest_collection_modifyitems(session, config, items):
    """Démarre un run dès qu'on a détecté un lab unique parmi les tests collectés."""
    if _is_disabled() or not items:
        return
    lab_path = _detect_lab_path(items)
    if lab_path is None:
        return

    try:
        with db.get_conn() as conn:
            run_id = db.insert_run_started(conn, lab_path)
        config._dsoxlab_run_id = run_id
        config._dsoxlab_lab_path = lab_path
    except Exception:
        # On ne casse jamais pytest si la DB est indisponible.
        pass


def pytest_runtest_logreport(report):
    """Inscrit chaque test (call phase uniquement) dans la table test_results."""
    if _is_disabled():
        return
    if report.when != "call" and not (report.when == "setup" and report.skipped):
        return

    config = report.session.config if hasattr(report, "session") else None
    # report n'a pas .session sur certains hooks ; on récupère via __pytest_config
    # mais le plus simple est de stocker le run_id dans pytest_sessionstart.
    # Ici on ne fait rien : la finalisation se fait dans sessionfinish.


def pytest_sessionfinish(session, exitstatus):
    """Finalise le run avec les compteurs de la session."""
    if _is_disabled():
        return
    config = session.config
    run_id = getattr(config, "_dsoxlab_run_id", None)
    if run_id is None:
        return

    # pytest stocke les stats dans session._fixturemanager... non, on parcourt _result.
    stats = {}
    for name in ("passed", "failed", "skipped", "error"):
        items = session.config.pluginmanager.getplugin("terminalreporter") or None
        if items is not None and hasattr(items, "stats"):
            stats[name] = len(items.stats.get(name, []))
        else:
            stats[name] = 0

    passed = stats.get("passed", 0)
    failed = stats.get("failed", 0) + stats.get("error", 0)
    skipped = stats.get("skipped", 0)
    total = passed + failed + skipped

    try:
        with db.get_conn() as conn:
            db.finalize_run(
                conn,
                run_id,
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
            )
    except Exception:
        pass
