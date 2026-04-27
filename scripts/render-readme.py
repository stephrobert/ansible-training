#!/usr/bin/env python3
"""Génère la liste des labs du README.md racine depuis meta.yml.

Le README a deux marqueurs HTML qui délimitent la zone à régénérer :

    <!-- LABS_LIST_START -->
    ... (contenu généré, ne pas éditer à la main) ...
    <!-- LABS_LIST_END -->

Usage :
    scripts/render-readme.py             # met à jour README.md
    scripts/render-readme.py --check     # vérifie que README.md est à jour (CI)
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
META_YML = REPO_ROOT / "meta.yml"
README_MD = REPO_ROOT / "README.md"

START_MARKER = "<!-- LABS_LIST_START -->"
END_MARKER = "<!-- LABS_LIST_END -->"


def load_meta() -> dict:
    with META_YML.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def lab_dirname_from_id(lab_id: str, section_id: str) -> str:
    """Réplique compute_lab_dirname du script de migration."""
    prefix = f"{section_id}-"
    if lab_id.startswith(prefix):
        stripped = lab_id[len(prefix):]
        if len(stripped) >= 3:
            return stripped
    return lab_id


def lab_short_title(lab_id: str, section_id: str) -> str:
    """Titre humain à partir de l'ID lab (sans préfixe section, espaces, capitalize)."""
    dirname = lab_dirname_from_id(lab_id, section_id)
    return dirname.replace("-", " ")


def render_section(section: dict) -> list[str]:
    """Rend une section en liste de lignes Markdown."""
    lines = []
    title = section["title"]
    desc = section.get("description", "")
    sect_id = section["id"]

    lines.append(f"### {title}")
    lines.append("")
    if desc:
        lines.append(desc)
        lines.append("")

    for lab_id in section["labs"]:
        dirname = lab_dirname_from_id(lab_id, sect_id)
        path = f"labs/{sect_id}/{dirname}"
        title_human = lab_short_title(lab_id, sect_id)
        lines.append(f"- [`{title_human}`](./{path}/)")

    lines.append("")
    return lines


def render_labs_list(meta: dict) -> str:
    """Rend la liste complète des labs (toutes sections)."""
    lines = []
    total_labs = sum(len(s["labs"]) for s in meta["sections"])
    lines.append(f"**{total_labs} labs** répartis en **{len(meta['sections'])} sections** "
                 f"(source de vérité : [`meta.yml`](./meta.yml)).")
    lines.append("")
    for section in meta["sections"]:
        lines.extend(render_section(section))
    return "\n".join(lines).rstrip() + "\n"


def update_readme(rendered: str, check_only: bool = False) -> bool:
    """Met à jour la zone marquée dans README.md.

    Retourne True si modification (ou si différence en mode check).
    """
    if not README_MD.exists():
        print(f"ERREUR : {README_MD} introuvable.", file=sys.stderr)
        sys.exit(1)

    content = README_MD.read_text(encoding="utf-8")

    pattern = re.compile(
        re.escape(START_MARKER) + r"\n.*?\n" + re.escape(END_MARKER),
        re.DOTALL,
    )

    new_block = f"{START_MARKER}\n\n{rendered}\n{END_MARKER}"

    if not pattern.search(content):
        print(f"ERREUR : marqueurs {START_MARKER} / {END_MARKER} absents de README.md.",
              file=sys.stderr)
        print("Ajoutez-les manuellement à l'endroit où la liste des labs doit apparaître.",
              file=sys.stderr)
        sys.exit(1)

    new_content = pattern.sub(new_block, content)

    if check_only:
        if new_content != content:
            print("README.md n'est pas à jour. Lancez : scripts/render-readme.py")
            return True
        print("README.md à jour.")
        return False

    if new_content != content:
        README_MD.write_text(new_content, encoding="utf-8")
        print(f"✅ README.md mis à jour.")
        return True
    print("README.md déjà à jour, rien à faire.")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="vérifie sans modifier (utile en CI)")
    args = ap.parse_args()

    meta = load_meta()
    rendered = render_labs_list(meta)
    changed = update_readme(rendered, check_only=args.check)

    if args.check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
