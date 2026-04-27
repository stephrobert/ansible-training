"""CLI principale `dsoxlab` (argparse + Rich).

Commandes :
- show     : tableau de bord (par défaut)
- next     : suggère le prochain lab à attaquer
- stats    : statistiques agrégées par section
- reset    : efface l'historique d'un lab (ou tout)
- export   : export JSON pour formateur/agrégation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from . import db, meta, views


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dsoxlab",
        description="Suivi d'avancement des labs Ansible-Training.",
    )
    sub = parser.add_subparsers(dest="command")

    # show (default)
    p_show = sub.add_parser("show", help="Tableau de bord par section/lab.")
    p_show.add_argument("--section", help="Filtrer une section (id meta.yml).")
    p_show.add_argument(
        "--status",
        choices=["completed", "in_progress", "failed", "not_started", "skipped"],
        help="Filtrer par statut.",
    )

    # next
    sub.add_parser("next", help="Suggère le prochain lab à attaquer.")

    # stats
    sub.add_parser("stats", help="Stats agrégées par section.")

    # reset
    p_reset = sub.add_parser("reset", help="Efface l'historique d'un lab ou tout.")
    p_reset.add_argument("--lab", help="Path du lab : <section>/<dirname>.")
    p_reset.add_argument("--all", action="store_true", help="Reset complet.")
    p_reset.add_argument("-y", "--yes", action="store_true", help="Pas de confirmation.")

    # export
    p_export = sub.add_parser("export", help="Export JSON de la progression.")
    p_export.add_argument("--output", "-o", type=Path, help="Fichier de sortie.")

    # lab : affiche le README d'un lab en rendu Rich
    p_lab = sub.add_parser("lab", help="Affiche le README d'un lab en rendu Markdown riche.")
    p_lab.add_argument("path", help="Path du lab : <section>/<dirname>.")
    p_lab.add_argument(
        "-c", "--challenge", action="store_true",
        help="Affiche challenge/README.md au lieu du tutoriel.",
    )
    p_lab.add_argument(
        "-b", "--both", action="store_true",
        help="Affiche README.md puis challenge/README.md.",
    )
    p_lab.add_argument(
        "-w", "--width", type=int, default=0,
        help="Largeur max d'affichage en caractères (défaut : 0 = largeur native du "
             "terminal, recommandé pour ne pas couper les commandes longues). "
             "Forcer ex. 80 ou 100 pour un rendu 'livre' compact.",
    )
    p_lab.add_argument(
        "--no-pager", action="store_true",
        help="Désactive le pager (less). Par défaut : pager activé sur TTY. "
             "Les liens externes sont toujours affichés en clair après le pager "
             "pour permettre CTRL+click une fois le pager fermé.",
    )

    return parser


def cmd_show(args, console: Console) -> int:
    repo = meta.load_repo()
    with db.get_conn() as conn:
        runs = db.last_run_per_lab(conn)
    views.render_overview(
        console, repo, runs,
        section_filter=args.section,
        status_filter=args.status,
    )
    return 0


def cmd_next(args, console: Console) -> int:
    repo = meta.load_repo()
    with db.get_conn() as conn:
        runs = db.last_run_per_lab(conn)
    views.render_next(console, repo, runs)
    return 0


def cmd_stats(args, console: Console) -> int:
    repo = meta.load_repo()
    with db.get_conn() as conn:
        runs = db.last_run_per_lab(conn)
    views.render_stats(console, repo, runs)
    return 0


def cmd_reset(args, console: Console) -> int:
    if not args.all and not args.lab:
        console.print("[red]Erreur :[/red] précise --lab <path> ou --all.")
        return 1
    if args.all and args.lab:
        console.print("[red]Erreur :[/red] --lab et --all sont mutuellement exclusifs.")
        return 1

    if args.all:
        if not args.yes and not Confirm.ask("Effacer TOUT l'historique ?", default=False):
            console.print("Annulé.")
            return 0
        with db.get_conn() as conn:
            n = db.reset_all(conn)
        console.print(f"[green]✓[/green] {n} run(s) supprimé(s).")
        return 0

    repo = meta.load_repo()
    lab = meta.find_lab_by_path(repo, args.lab)
    if lab is None:
        console.print(f"[red]Erreur :[/red] lab '{args.lab}' inconnu (vérifie meta.yml).")
        return 1

    if not args.yes and not Confirm.ask(
        f"Effacer l'historique de [cyan]{lab.path}[/cyan] ?", default=False
    ):
        console.print("Annulé.")
        return 0

    with db.get_conn() as conn:
        n = db.reset_lab(conn, lab.path)
    console.print(f"[green]✓[/green] {n} run(s) supprimé(s) pour {lab.path}.")
    return 0


def cmd_lab(args, console: Console) -> int:
    """Affiche le README d'un lab en rendu Markdown Rich."""
    import os
    import re
    import shutil
    import sys

    from contextlib import contextmanager

    from rich.markdown import Markdown
    from rich.rule import Rule

    repo = meta.load_repo()
    lab = meta.find_lab_by_path(repo, args.path)
    if lab is None:
        console.print(f"[red]Erreur :[/red] lab '{args.path}' inconnu.")
        console.print("[dim]Astuce : 'dsoxlab show' liste les chemins valides.[/dim]")
        return 1

    repo_root = meta.find_repo_root()
    lab_dir = repo_root / "labs" / lab.path
    readme = lab_dir / "README.md"
    challenge_readme = lab_dir / "challenge" / "README.md"

    # Largeur du rendu Markdown.
    # On capture la largeur réelle du terminal AVANT que le pager ne soit lancé
    # (sinon Rich voit stdout=pipe → fallback 80 cols → commandes longues coupées).
    if args.width and args.width > 0:
        width = args.width
    else:
        width = shutil.get_terminal_size(fallback=(120, 24)).columns
    render_console = Console(width=width)

    # Pager activé par défaut sur TTY (--no-pager pour désactiver).
    # less -R : conserve les codes ANSI (couleurs Rich) mais pas les hyperlinks
    # OSC-8. C'est pour ça qu'on affiche les liens en clair APRÈS le pager.
    use_pager = sys.stdout.isatty() and not args.no_pager
    if use_pager and "PAGER" not in os.environ and "LESS" not in os.environ:
        os.environ["LESS"] = "-R"

    @contextmanager
    def _maybe_pager():
        if use_pager:
            with render_console.pager(styles=True):
                yield
        else:
            yield

    # Liens externes : extraction + injection inline pour qu'ils soient
    # visibles DANS le pager (less ne supporte pas OSC-8 hyperlinks).
    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    collected_links: list[tuple[str, str]] = []

    def _expand_external_urls(md: str) -> str:
        """Transforme `[label](url)` en `[label](url) <url-en-clair>`.

        Saute les blocs de code triple-backtick. URLs internes (./..., #...)
        non touchées car le pattern matche http(s) seulement.
        """
        out = []
        in_code = False
        for line in md.splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code = not in_code
                out.append(line)
                continue
            if in_code:
                out.append(line)
                continue
            # Injecte l'URL en clair (entre backticks pour Rich code-style)
            # APRÈS le lien markdown. Le label reste cliquable, l'URL visible.
            out.append(link_pattern.sub(r"[\1](\2) `\2`", line))
        return "".join(out)

    def _collect_links_from_text(text: str) -> None:
        for label, url in link_pattern.findall(text):
            if (label, url) not in collected_links:
                collected_links.append((label, url))

    def _render(path: Path, title: str) -> bool:
        if not path.exists():
            render_console.print(f"[yellow]⚠[/yellow] {path.relative_to(repo_root)} absent.")
            return False
        raw = path.read_text(encoding="utf-8")
        _collect_links_from_text(raw)
        rendered = _expand_external_urls(raw)
        render_console.print(Rule(title=title, style="cyan"))
        render_console.print()
        render_console.print(Markdown(rendered, code_theme="monokai"))
        render_console.print()
        return True

    # Choix du / des fichiers à rendre
    targets: list[tuple[Path, str]] = []
    if args.both:
        targets = [
            (readme, f"📖 {lab.path} — Tutoriel"),
            (challenge_readme, f"🎯 {lab.path} — Challenge"),
        ]
    elif args.challenge:
        targets = [(challenge_readme, f"🎯 {lab.path} — Challenge")]
    else:
        targets = [(readme, f"📖 {lab.path} — Tutoriel")]

    # Pré-collecte des liens (extraits AVANT le rendu pour les afficher en
    # header). Note : `_render` les re-collecte aussi mais l'idempotence
    # (pas de doublons) gère le cas.
    for path, _ in targets:
        if path.exists():
            _collect_links_from_text(path.read_text(encoding="utf-8"))

    def _clean_label(s: str) -> str:
        return re.sub(r"[*_`]", "", s).strip()

    def _render_header() -> None:
        """Header visible dès l'ouverture du pager : URLs en clair."""
        if not collected_links:
            return
        render_console.print(Rule(title="🔗 Liens externes du guide", style="cyan", align="left"))
        for label, url in collected_links:
            render_console.print(f"  • [bold]{_clean_label(label)}[/bold]")
            render_console.print(
                f"    [cyan]{url}[/cyan]", soft_wrap=True, overflow="ignore"
            )
        render_console.print()
        render_console.print(
            "[dim]💡 CTRL+click sur l'URL (hors pager) ou copier-coller dans le navigateur.[/dim]"
        )
        render_console.print()

    with _maybe_pager():
        _render_header()
        for path, title in targets:
            _render(path, title)

    return 0

    # Footer : commande pour basculer
    if not args.both:
        other = "Challenge" if not args.challenge else "Tutoriel"
        flag = "-c" if not args.challenge else ""
        console.print(
            f"[dim]→ Voir le {other.lower()} : "
            f"bin/dsoxlab lab {args.path} {flag}[/dim]"
        )
    return 0


def cmd_export(args, console: Console) -> int:
    repo = meta.load_repo()
    with db.get_conn() as conn:
        runs = db.last_run_per_lab(conn)
    payload = {
        "repo": {
            "id": repo.id,
            "category": repo.category,
            "title": repo.title,
        },
        "labs": [
            {
                "path": lab.path,
                "section": lab.section_id,
                "status": (run["status"] if (run := runs.get(lab.path)) else "not_started"),
                "score_percent": (run["score_percent"] if run else None),
                "last_run_at": (run["started_at"] if run else None),
                "tests_passed": (run["tests_passed"] if run else None),
                "tests_total": (run["tests_total"] if run else None),
            }
            for sect in repo.sections
            for lab in sect.labs
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
        console.print(f"[green]✓[/green] Exporté vers {args.output}")
    else:
        print(text)
    return 0


COMMANDS = {
    "show": cmd_show,
    "next": cmd_next,
    "stats": cmd_stats,
    "reset": cmd_reset,
    "export": cmd_export,
    "lab": cmd_lab,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    console = Console()

    cmd = args.command or "show"
    if cmd not in COMMANDS:
        parser.print_help()
        return 1

    # Si la commande default 'show' a besoin d'attributs absents, les ajouter.
    if cmd == "show" and not hasattr(args, "section"):
        args.section = None
        args.status = None

    try:
        return COMMANDS[cmd](args, console)
    except FileNotFoundError as e:
        console.print(f"[red]Erreur :[/red] {e}")
        return 2
    except BrokenPipeError:
        # Pipe fermé en aval (head, grep -m, less qui quitte tôt).
        # Comportement standard Unix : sortir silencieusement avec 0.
        # Voir https://docs.python.org/3/library/signal.html#note-on-sigpipe
        try:
            sys.stdout.close()
        except Exception:
            pass
        try:
            sys.stderr.close()
        except Exception:
            pass
        return 0
    except KeyboardInterrupt:
        # Ctrl-C dans le pager ou pendant rendu : sortie propre.
        console.print()
        return 130


if __name__ == "__main__":
    sys.exit(main())
