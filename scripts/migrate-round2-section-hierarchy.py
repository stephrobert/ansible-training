#!/usr/bin/env python3
"""Migration round 2 : labs/<id-stable>/ → labs/<section>/<lab>/

Lit meta.yml pour savoir quel lab va dans quelle section, puis :
- mv labs/<id> → labs/<section>/<lab>  (lab = id sans préfixe section quand possible)
- mv solution/<id> → solution/<section>/<lab>
- sed sur tous les fichiers texte qui référencent labs/<id> ou solution/<id>
- ajoute aux redirects.csv existant

Usage :
    scripts/migrate-round2-section-hierarchy.py --dry-run
    scripts/migrate-round2-section-hierarchy.py
"""

import argparse
import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
META_YML = REPO_ROOT / "meta.yml"


def load_meta() -> dict:
    """Charge meta.yml."""
    with META_YML.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_lab_dirname(lab_id: str, section_id: str) -> str:
    """Calcule le nom du dossier lab dans <section>/.

    Si lab_id commence par <section_id>-, retire ce préfixe.
    Sinon garde lab_id tel quel.
    """
    prefix = f"{section_id}-"
    if lab_id.startswith(prefix):
        stripped = lab_id[len(prefix):]
        # Garde-fou : si le résultat est vide ou trop court, on garde l'ID complet
        if len(stripped) < 3:
            return lab_id
        return stripped
    return lab_id


def build_mapping(meta: dict) -> list[tuple[str, str, str, str]]:
    """Liste de (lab_id, section_id, new_path_relative, lab_dirname)."""
    pairs = []
    for section in meta["sections"]:
        sect_id = section["id"]
        for lab_id in section["labs"]:
            dirname = compute_lab_dirname(lab_id, sect_id)
            new_path = f"{sect_id}/{dirname}"
            pairs.append((lab_id, sect_id, new_path, dirname))
    return pairs


def detect_collisions(pairs) -> dict:
    """Vérifie qu'aucun chemin de destination n'est dupliqué."""
    seen = {}
    for lab_id, sect, new_path, _ in pairs:
        seen.setdefault(new_path, []).append(lab_id)
    return {k: v for k, v in seen.items() if len(v) > 1}


def append_redirects(pairs, csv_path: Path) -> None:
    """Append les nouvelles redirections (round 2) au CSV."""
    new_rows = []
    for lab_id, sect, new_path, _ in pairs:
        new_rows.append([f"labs/{lab_id}", f"labs/{new_path}", lab_id, new_path])

    # Lire l'existant si présent
    existing_rows = []
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.reader(f)
            existing_rows = list(reader)

    # Si l'header est déjà là, ne pas le recréer ; ajouter les rows round 2
    if existing_rows and existing_rows[0][0] == "old_path":
        merged = existing_rows + new_rows
    else:
        merged = [["old_path", "new_path", "old_id", "new_id"]] + new_rows

    with csv_path.open("w", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(merged)


def rename_dirs(pairs, base: str, dry_run: bool) -> int:
    """Renomme labs/<id> → labs/<section>/<dirname>."""
    base_dir = REPO_ROOT / base
    if not base_dir.exists():
        return 0

    renamed = 0
    for lab_id, sect, _, dirname in pairs:
        src = base_dir / lab_id
        dst_section = base_dir / sect
        dst = dst_section / dirname

        if not src.exists():
            # peut être normal pour solution/ (tous les labs n'y sont pas)
            continue
        if dst.exists():
            print(f"  ⚠ déjà présent : {base}/{sect}/{dirname}")
            continue

        print(f"  mv {base}/{lab_id} → {base}/{sect}/{dirname}")
        if not dry_run:
            dst_section.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        renamed += 1

    return renamed


def replace_in_files(pairs, dry_run: bool) -> int:
    """Remplace labs/<old> → labs/<section>/<dirname> dans les fichiers texte.

    Tri par longueur décroissante d'old pour éviter les remplacements partiels.
    """
    # Tri descendant par longueur du lab_id pour éviter les chevauchements
    sorted_pairs = sorted(pairs, key=lambda p: len(p[0]), reverse=True)

    suffixes = (".md", ".yml", ".yaml", ".py", ".sh", ".cfg", ".j2", ".txt")
    candidates = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
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
        for lab_id, sect, _, dirname in sorted_pairs:
            new_rel = f"{sect}/{dirname}"
            if lab_id == new_rel:
                continue
            content = content.replace(f"labs/{lab_id}", f"labs/{new_rel}")
            content = content.replace(f"solution/{lab_id}", f"solution/{new_rel}")
        if content != original:
            modified += 1
            if not dry_run:
                path.write_text(content, encoding="utf-8")

    return modified


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    meta = load_meta()
    pairs = build_mapping(meta)
    print(f"Mapping calculé : {len(pairs)} labs.\n")

    collisions = detect_collisions(pairs)
    if collisions:
        print("❌ COLLISIONS détectées :")
        for path, labs in collisions.items():
            print(f"  {path} ← {labs}")
        sys.exit(1)
    print("✅ Aucune collision.\n")

    # Aperçu mapping
    print("=== Mapping (extraits) ===")
    for lab_id, sect, new_path, dirname in pairs[:10]:
        print(f"  {lab_id:50s} → {new_path}")
    print(f"  ... {len(pairs) - 10} autres ...\n")

    # Append redirections
    redirects_csv = REPO_ROOT / "docs" / "refactor-redirects.csv"
    if not args.dry_run:
        append_redirects(pairs, redirects_csv)
        print(f"✅ Redirections round 2 ajoutées dans {redirects_csv.relative_to(REPO_ROOT)}\n")

    # Renommage
    print("=== Renommage labs/ ===")
    n_labs = rename_dirs(pairs, "labs", args.dry_run)
    print(f"Total : {n_labs} labs renommés.\n")

    print("=== Renommage solution/ ===")
    n_sol = rename_dirs(pairs, "solution", args.dry_run)
    print(f"Total : {n_sol} solutions renommées.\n")

    # Remplacement dans fichiers texte
    print("=== Remplacement dans fichiers ===")
    n_files = replace_in_files(pairs, args.dry_run)
    print(f"Total : {n_files} fichiers modifiés.\n")

    if args.dry_run:
        print("✅ Dry-run terminé. Relance sans --dry-run pour appliquer.")
    else:
        print("✅ Migration round 2 terminée.")
        print("   Étapes suivantes :")
        print("   1. Vérifier `git status` (revue).")
        print("   2. Lancer `pytest --collect-only labs/` pour valider.")
        print("   3. Adapter conftest.py (_find_lab_root pour 2 niveaux + clés _EXTRA_*).")


if __name__ == "__main__":
    main()
