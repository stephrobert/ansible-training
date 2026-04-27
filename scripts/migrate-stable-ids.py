#!/usr/bin/env python3
"""Migration : labs/<NN>[a-z]-<slug>/ → labs/<stable-id>/

Génère le mapping `<old> → <new>`, écrit redirects.csv (pour mise à jour
des guides blog), puis fait les `mv` sur labs/, solution/ et tous les
fichiers texte qui référencent les anciens chemins.

Usage :
    scripts/migrate-stable-ids.py --dry-run    # juste afficher
    scripts/migrate-stable-ids.py              # exécuter
"""

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Exceptions : préfixe à modifier après retrait du numéro.
# Format : ancien-slug-sans-numéro → nouvelle valeur (ID stable).
RENAME_EXCEPTIONS = {
    # Bootstrap : ajouter prefix
    "prepare-managed-nodes": "bootstrap-prepare-managed-nodes",
    # Section "Tests Molecule" : retirer le préfixe roles-
    "roles-molecule-introduction": "molecule-introduction",
    "roles-molecule-installation-config": "molecule-installation-config",
    "roles-molecule-tdd-cycle": "molecule-tdd-cycle",
    "roles-molecule-scenarios-multi-distro": "molecule-scenarios-multi-distro",
    # Section "Tests Python & lint" : préfixe roles- → tests-
    "roles-tests-testinfra": "tests-testinfra",
    "roles-tests-tox-multiversion": "tests-tox-multiversion",
    "roles-ansible-lint-production": "tests-ansible-lint-production",
    # Section "CI/CD" : préfixe roles- → ci-
    "roles-ci-github-actions": "ci-github-actions",
    "roles-ci-gitlab": "ci-gitlab",
    # Section "Galaxy" : préfixe roles- → galaxy-
    "roles-ansible-galaxy-cli": "galaxy-ansible-galaxy-cli",
    "roles-installer-roles-galaxy": "galaxy-installer-roles",
    "roles-auditer-role-existant": "galaxy-auditer-role-existant",
    "roles-versionner-publier": "galaxy-versionner-publier",
    # Section "Pratiques avancées"
    "ansible-pull-gitops": "pratiques-ansible-pull-gitops",
}

# Pattern d'un nom de lab : 000- ou 04b- ou 100- → numéro + tiret.
NUM_PREFIX_RE = re.compile(r"^\d{1,3}[a-z]?-")


def compute_new_id(old_name: str) -> str:
    """Compute stable ID from old labs/ folder name."""
    # Retirer le préfixe numérique : "04b-premiers-pas-..." → "premiers-pas-..."
    stripped = NUM_PREFIX_RE.sub("", old_name)
    # Appliquer exception si présente
    return RENAME_EXCEPTIONS.get(stripped, stripped)


def build_mapping() -> list[tuple[str, str]]:
    """Liste de (old_name, new_id) pour tous les labs."""
    labs_dir = REPO_ROOT / "labs"
    pairs = []
    for entry in sorted(labs_dir.iterdir()):
        if not entry.is_dir():
            continue
        old_name = entry.name
        new_id = compute_new_id(old_name)
        pairs.append((old_name, new_id))
    return pairs


def detect_collisions(pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Vérifie qu'aucun new_id n'est dupliqué."""
    seen: dict[str, list[str]] = {}
    for old, new in pairs:
        seen.setdefault(new, []).append(old)
    return {k: v for k, v in seen.items() if len(v) > 1}


def write_redirects_csv(pairs: list[tuple[str, str]], out_path: Path) -> None:
    """Écrit le CSV de redirection pour les guides blog."""
    with out_path.open("w", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["old_path", "new_path", "old_id", "new_id"])
        for old, new in pairs:
            w.writerow([f"labs/{old}", f"labs/{new}", old, new])


def replace_in_files(pairs: list[tuple[str, str]], dry_run: bool) -> int:
    """Remplace toutes les occurrences `labs/<old>` par `labs/<new>` dans les fichiers texte.

    Retourne le nombre de fichiers modifiés.
    """
    # Tri : remplacer d'abord les noms les plus longs pour éviter
    # les remplacements partiels (ex: '04-premier' avant '04').
    sorted_pairs = sorted(pairs, key=lambda p: len(p[0]), reverse=True)

    # Trouver tous les fichiers texte qui référencent au moins un ancien chemin.
    suffixes = (".md", ".yml", ".yaml", ".py", ".sh", ".cfg", ".j2", ".txt")
    candidates = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        # Skip git, node_modules, __pycache__, .venv, .ansible
        parts = path.parts
        if any(p.startswith(".") and p not in (".github", ".gitlab-ci.yml")
               for p in parts):
            continue
        if "__pycache__" in parts or ".git" in parts:
            continue
        if not (path.suffix in suffixes or path.name == "Makefile"):
            continue
        candidates.append(path)

    modified = 0
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = content
        for old, new in sorted_pairs:
            if old == new:
                continue
            content = content.replace(f"labs/{old}", f"labs/{new}")
            content = content.replace(f"solution/{old}", f"solution/{new}")
        if content != original:
            modified += 1
            if not dry_run:
                path.write_text(content, encoding="utf-8")
            print(f"  M {path.relative_to(REPO_ROOT)}")
    return modified


def rename_dirs(pairs: list[tuple[str, str]], base: str, dry_run: bool) -> int:
    """Renomme les dossiers labs/<old> → labs/<new> et solution/<old> → solution/<new>."""
    base_dir = REPO_ROOT / base
    if not base_dir.exists():
        return 0
    renamed = 0
    for old, new in pairs:
        if old == new:
            continue
        src = base_dir / old
        dst = base_dir / new
        if src.exists() and not dst.exists():
            print(f"  mv {base}/{old} → {base}/{new}")
            if not dry_run:
                src.rename(dst)
            renamed += 1
        elif dst.exists() and not src.exists():
            # déjà migré
            pass
        elif not src.exists():
            # n'existe pas dans ce base (normal pour solution/, pas tous les labs y sont)
            pass
    return renamed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="afficher sans modifier")
    args = ap.parse_args()

    pairs = build_mapping()
    print(f"Mapping calculé : {len(pairs)} labs.\n")

    # Vérif collisions
    collisions = detect_collisions(pairs)
    if collisions:
        print("❌ COLLISIONS détectées (plusieurs anciens labs → même nouvel ID) :")
        for new_id, olds in collisions.items():
            print(f"  {new_id} ← {olds}")
        sys.exit(1)
    print("✅ Aucune collision d'ID.\n")

    # Écrire redirects.csv
    redirects = REPO_ROOT / "docs" / "refactor-redirects.csv"
    if not args.dry_run:
        write_redirects_csv(pairs, redirects)
        print(f"✅ Redirections écrites dans {redirects.relative_to(REPO_ROOT)}\n")
    else:
        print(f"(dry-run) Redirections seraient écrites dans {redirects.relative_to(REPO_ROOT)}\n")

    # Renommer labs/
    print("=== Renommage labs/ ===")
    n_labs = rename_dirs(pairs, "labs", args.dry_run)
    print(f"Total : {n_labs} labs renommés.\n")

    # Renommer solution/
    print("=== Renommage solution/ ===")
    n_sol = rename_dirs(pairs, "solution", args.dry_run)
    print(f"Total : {n_sol} solutions renommées.\n")

    # Remplacer dans les fichiers texte
    print("=== Remplacement dans fichiers texte ===")
    n_files = replace_in_files(pairs, args.dry_run)
    print(f"Total : {n_files} fichiers modifiés.\n")

    if args.dry_run:
        print("✅ Dry-run terminé. Relance sans --dry-run pour appliquer.")
    else:
        print("✅ Migration terminée.")
        print("   Étapes suivantes :")
        print("   1. Vérifier `git status` (revue des changements).")
        print("   2. Lancer `pytest --collect-only labs/` pour valider.")
        print("   3. Adapter conftest.py manuellement (constantes _EXTRA_ARGS / _EXTRA_ENV).")
        print("   4. Créer meta.yml + scripts/render-readme.py.")


if __name__ == "__main__":
    main()
