#!/usr/bin/env python3
"""Génère la liste des labs des README racine depuis meta.yml.

Le README a deux marqueurs HTML qui délimitent la zone à régénérer :

    <!-- LABS_LIST_START -->
    ... (contenu généré, ne pas éditer à la main) ...
    <!-- LABS_LIST_END -->

Usage :
    scripts/render-readme.py             # met à jour README.md et README.fr.md
    scripts/render-readme.py --check     # vérifie que les deux sont à jour (CI)
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
META_YML = REPO_ROOT / "meta.yml"
#: Le dépôt est bilingue : la liste est régénérée dans les deux README, à
#: l'identique de linux-dsoxlab-training. Une seule langue tenue à jour
#: laisserait l'autre moitié des lecteurs sur un catalogue périmé.
TARGETS = {"README.md": "en", "README.fr.md": "fr"}

START_MARKER = "<!-- LABS_LIST_START -->"
END_MARKER = "<!-- LABS_LIST_END -->"


def load_meta() -> dict:
    with META_YML.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def lab_short_title(lab_rel: str) -> str:
    """Titre humain à partir du chemin du lab (dernier segment, tirets en espaces)."""
    return lab_rel.split("/")[-1].replace("-", " ")


def render_section(section: dict, lang: str = "fr") -> list[str]:
    """Rend une section en liste de lignes Markdown.

    Le meta.yml peut porter ``title_en`` et ``description_en`` ; à défaut, la
    version française sert aux deux, ce qui vaut mieux qu'une section vide.
    """
    lines = []
    if lang == "en":
        title = section.get("title_en") or section["title"]
        desc = section.get("description_en") or section.get("description", "")
    else:
        title = section["title"]
        desc = section.get("description", "")

    lines.append(f"### {title}")
    lines.append("")
    if desc:
        lines.append(desc)
        lines.append("")

    # Depuis le passage au contrat dsoxlab 0.1.6, meta.yml porte des chemins
    # relatifs à labs/ (decouvrir/installation-ansible) et non plus des ids
    # préfixés : il n'y a plus de nom de répertoire à reconstruire.
    for lab_rel in section["labs"]:
        lines.append(f"- [`{lab_short_title(lab_rel)}`](./labs/{lab_rel}/)")

    lines.append("")
    return lines


def render_labs_list(meta: dict, lang: str = "fr") -> str:
    """Rend la liste complète des labs (toutes sections), dans la langue voulue."""
    lines = []
    total_labs = sum(len(s["labs"]) for s in meta["sections"])
    n_sections = len(meta["sections"])
    if lang == "en":
        lines.append(f"**{total_labs} labs** across **{n_sections} sections** "
                     f"(source of truth: [`meta.yml`](./meta.yml)).")
    else:
        lines.append(f"**{total_labs} labs** répartis en **{n_sections} sections** "
                     f"(source de vérité : [`meta.yml`](./meta.yml)).")
    lines.append("")
    for section in meta["sections"]:
        lines.extend(render_section(section, lang))
    return "\n".join(lines).rstrip() + "\n"


def update_readme(meta: dict, check_only: bool = False) -> bool:
    """Met à jour la zone marquée dans chaque README de TARGETS.

    Retourne True si au moins un fichier est périmé (mode check) ou a été
    réécrit. Les deux langues sont traitées d'un bloc : régénérer une seule
    laisserait l'autre catalogue mentir en silence.
    """
    perimes: list[str] = []
    for nom, lang in TARGETS.items():
        chemin = REPO_ROOT / nom
        if not chemin.exists():
            print(f"ERREUR : {chemin} introuvable.", file=sys.stderr)
            sys.exit(1)

        contenu = chemin.read_text(encoding="utf-8")
        motif = re.compile(
            re.escape(START_MARKER) + r"\n.*?\n" + re.escape(END_MARKER),
            re.DOTALL,
        )
        if not motif.search(contenu):
            print(
                f"ERREUR : marqueurs {START_MARKER} / {END_MARKER} absents de {nom}.",
                file=sys.stderr,
            )
            print(
                "Ajoutez-les à l'endroit où la liste des labs doit apparaître.",
                file=sys.stderr,
            )
            sys.exit(1)

        bloc = f"{START_MARKER}\n\n{render_labs_list(meta, lang)}\n{END_MARKER}"
        neuf = motif.sub(bloc, contenu)

        if neuf != contenu:
            perimes.append(nom)
            if not check_only:
                chemin.write_text(neuf, encoding="utf-8")

    if check_only:
        if perimes:
            print(
                "Catalogue périmé dans : " + ", ".join(perimes)
                + "\nLancez : scripts/render-readme.py"
            )
            return True
        print("Catalogue à jour dans " + ", ".join(TARGETS))
        return False

    if perimes:
        print("✅ mis à jour : " + ", ".join(perimes))
        return True
    print("Déjà à jour, rien à faire.")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="vérifie sans modifier (utile en CI)")
    args = ap.parse_args()

    meta = load_meta()
    changed = update_readme(meta, check_only=args.check)

    if args.check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
