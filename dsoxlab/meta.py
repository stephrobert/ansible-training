"""Lecture de meta.yml — source de vérité de l'ordre des labs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Lab:
    """Un lab pédagogique."""
    id: str               # ex : "vault-introduction"
    section_id: str       # ex : "vault"
    dirname: str          # ex : "introduction"
    path: str             # ex : "vault/introduction"
    title: str            # ex : "introduction"


@dataclass
class Section:
    """Section pédagogique."""
    id: str
    title: str
    description: str
    labs: list[Lab]
    auto_run: bool = False    # True : section jouée auto (ex: bootstrap), `next` la skip


@dataclass
class Repo:
    """Métadonnées repo (depuis meta.yml:repo)."""
    id: str
    category: str
    title: str
    description: str
    blog_url: str
    sections: list[Section]


def _lab_dirname_from_id(lab_id: str, section_id: str) -> str:
    """Retire le préfixe section quand il matche."""
    prefix = f"{section_id}-"
    if lab_id.startswith(prefix):
        stripped = lab_id[len(prefix):]
        if len(stripped) >= 3:
            return stripped
    return lab_id


def _humanize_title(dirname: str) -> str:
    """`vs-imperatif` → `vs imperatif`."""
    return dirname.replace("-", " ")


def find_repo_root(start: Path | None = None) -> Path:
    """Trouve la racine du repo (première qui contient meta.yml)."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "meta.yml").exists():
            return parent
    raise FileNotFoundError(
        f"meta.yml introuvable depuis {cur}. Lance la CLI depuis le repo."
    )


def load_repo(meta_path: Path | None = None) -> Repo:
    """Charge meta.yml et retourne un Repo populé."""
    if meta_path is None:
        meta_path = find_repo_root() / "meta.yml"
    with meta_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    repo_meta = data.get("repo", {})
    sections = []
    for sect_data in data.get("sections", []):
        sect_id = sect_data["id"]
        labs = []
        for lab_id in sect_data["labs"]:
            dirname = _lab_dirname_from_id(lab_id, sect_id)
            labs.append(Lab(
                id=lab_id,
                section_id=sect_id,
                dirname=dirname,
                path=f"{sect_id}/{dirname}",
                title=_humanize_title(dirname),
            ))
        sections.append(Section(
            id=sect_id,
            title=sect_data["title"],
            description=sect_data.get("description", ""),
            labs=labs,
            auto_run=sect_data.get("auto_run", False),
        ))

    return Repo(
        id=repo_meta.get("id", "unknown"),
        category=repo_meta.get("category", "unknown"),
        title=repo_meta.get("title", ""),
        description=repo_meta.get("description", ""),
        blog_url=repo_meta.get("blog_url", ""),
        sections=sections,
    )


def all_labs(repo: Repo) -> list[Lab]:
    """Liste plate de tous les labs (dans l'ordre meta.yml)."""
    return [lab for sect in repo.sections for lab in sect.labs]


def find_lab_by_path(repo: Repo, path: str) -> Lab | None:
    """Cherche un lab par son `<section>/<dirname>` ou par son `<id>`."""
    for sect in repo.sections:
        for lab in sect.labs:
            if lab.path == path or lab.id == path:
                return lab
    return None
