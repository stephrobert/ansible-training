"""Rendu Rich de la progression."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .meta import Repo, Section, Lab


# Statut d'un lab basé sur le run le plus récent
STATUS_ICON = {
    "completed": "[green]✅[/green]",
    "in_progress": "[yellow]⏳[/yellow]",
    "failed": "[red]❌[/red]",
    "skipped": "[dim]⊘[/dim]",
    "not_started": "[dim]·[/dim]",
}

STATUS_LABEL = {
    "completed": "✅ ok",
    "in_progress": "⏳ wip",
    "failed": "❌ ko",
    "skipped": "⊘ skip",
    "not_started": "· -",
}


def _humanize_age(iso_ts: str | None) -> str:
    if not iso_ts:
        return "—"
    dt = datetime.fromisoformat(iso_ts)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = now - dt
    if delta.days >= 1:
        return f"il y a {delta.days} j"
    h = delta.seconds // 3600
    if h >= 1:
        return f"il y a {h} h"
    m = (delta.seconds % 3600) // 60
    if m >= 1:
        return f"il y a {m} min"
    return "à l'instant"


def _lab_status(run: sqlite3.Row | None) -> str:
    if run is None:
        return "not_started"
    return run["status"]


def render_overview(
    console: Console,
    repo: Repo,
    runs_by_lab: dict[str, sqlite3.Row],
    section_filter: str | None = None,
    status_filter: str | None = None,
) -> None:
    """Affiche le tableau de bord global ou filtré."""
    total_labs = sum(len(s.labs) for s in repo.sections)
    completed = sum(
        1 for run in runs_by_lab.values() if run["status"] == "completed"
    )
    in_progress = sum(
        1 for run in runs_by_lab.values() if run["status"] == "in_progress"
    )

    # En-tête
    header = Text()
    header.append(f"{repo.title}\n", style="bold cyan")
    header.append(f"Catégorie : {repo.category}  ·  ", style="dim")
    header.append(
        f"{completed}/{total_labs} labs passés ({100*completed//max(total_labs,1)} %)",
        style="bold green" if completed == total_labs else "bold",
    )
    header.append(f"  ·  {in_progress} en cours", style="yellow")
    console.print(Panel(header, expand=False))

    for section in repo.sections:
        if section_filter and section.id != section_filter:
            continue
        _render_section_table(console, section, runs_by_lab, status_filter)


def _render_section_table(
    console: Console,
    section: Section,
    runs_by_lab: dict[str, sqlite3.Row],
    status_filter: str | None,
) -> None:
    """Rendu d'une section sous forme de tableau."""
    # Filter rows by status
    rows = []
    for lab in section.labs:
        run = runs_by_lab.get(lab.path)
        status = _lab_status(run)
        if status_filter and status != status_filter:
            continue
        rows.append((lab, run, status))

    if not rows:
        return

    nb_done = sum(1 for _, _, s in rows if s == "completed")
    nb_total = len(section.labs)

    title = f"[bold]{section.title}[/bold]  [dim]({nb_done}/{nb_total})[/dim]"
    table = Table(
        title=title,
        title_justify="left",
        show_header=True,
        header_style="dim",
        expand=False,
    )
    table.add_column("", width=2)
    table.add_column("Lab", min_width=30)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Tests", justify="center", width=8)
    table.add_column("Updated", style="dim", width=14)

    for lab, run, status in rows:
        icon = STATUS_ICON.get(status, "?")
        score = (
            f"[green]{run['score_percent']:.0f} %[/green]"
            if status == "completed"
            else (
                f"[yellow]{run['score_percent']:.0f} %[/yellow]"
                if run is not None and run["score_percent"] is not None
                else "—"
            )
        )
        tests = (
            f"{run['tests_passed']}/{run['tests_total'] - run['tests_skipped']}"
            if run is not None and run["tests_total"]
            else "—"
        )
        updated = _humanize_age(run["started_at"]) if run is not None else "—"
        table.add_row(icon, lab.path, score, tests, updated)

    console.print(table)
    console.print()


def render_next(console: Console, repo: Repo, runs_by_lab: dict[str, sqlite3.Row]) -> None:
    """Suggère le prochain lab à travailler (premier non complété dans l'ordre meta.yml).

    Saute les sections marquées `auto_run: true` dans meta.yml (ex : bootstrap)
    qui ne sont pas pédagogiques.
    """
    for section in repo.sections:
        if section.auto_run:
            continue
        for lab in section.labs:
            run = runs_by_lab.get(lab.path)
            status = _lab_status(run)
            if status != "completed":
                body = Text.from_markup(
                    f"[bold]Prochain lab[/bold] : [cyan]{lab.path}[/cyan]\n"
                    f"  Section : {section.title}\n"
                    f"  Statut  : {STATUS_LABEL.get(status, status)}\n"
                    f"\n"
                    f"[dim]💡 Confort : [bold]ouvrez votre terminal en 2 colonnes[/bold] "
                    f"(tmux, VS Code, Terminator…)\n"
                    f"   → consigne à gauche, commandes à droite. Cf. README §[/dim]"
                    f" [italic]Configuration recommandée[/italic]\n"
                    f"\n"
                    f"[bold underline]Workflow recommandé[/bold underline]\n"
                    f"\n"
                    f"  [bold]1.[/bold] 📖 [bold]Lire le tutoriel guidé[/bold]\n"
                    f"     [dim]$[/dim] dsoxlab lab [cyan]{lab.path}[/cyan]\n"
                    f"\n"
                    f"  [bold]2.[/bold] ✍️  [bold]Écrire votre [italic]lab.yml[/italic][/bold] en suivant les exercices\n"
                    f"     [dim]→ fichier à créer : [/dim][cyan]lab.yml[/cyan] [dim](à la racine du lab)[/dim]\n"
                    f"\n"
                    f"  [bold]3.[/bold] 🎯 [bold]Lire la consigne du challenge[/bold]\n"
                    f"     [dim]$[/dim] dsoxlab lab [cyan]{lab.path}[/cyan] -c\n"
                    f"\n"
                    f"  [bold]4.[/bold] ✍️  [bold]Écrire votre [italic]challenge/solution.yml[/italic][/bold] [dim](squelette ??? à compléter)[/dim]\n"
                    f"\n"
                    f"  [bold]5.[/bold] 🚀 [bold]Lancer la solution puis valider[/bold]\n"
                    f"     [dim]$[/dim] cd labs/[cyan]{lab.path}[/cyan]\n"
                    f"     [dim]$[/dim] ansible-playbook challenge/solution.yml\n"
                    f"     [dim]$[/dim] pytest -v challenge/tests/   [dim]# inscrit auto le score[/dim]\n"
                    f"\n"
                    f"  [bold]6.[/bold] 🧹 [bold]Rejouer à blanc si besoin[/bold]\n"
                    f"     [dim]$[/dim] make clean\n"
                    f"\n"
                    f"[dim]💡 Bloqué ? Le formateur peut décrypter une solution officielle :\n"
                    f"   [italic]make solve LAB={lab.path}[/italic] (nécessite .vault-pass)[/dim]"
                )
                console.print(Panel.fit(
                    body,
                    title="🎯 Prochaine étape",
                    border_style="cyan",
                ))
                return
    console.print("[bold green]✓ Tous les labs sont passés. Bravo ![/bold green]")


def render_stats(console: Console, repo: Repo, runs_by_lab: dict[str, sqlite3.Row]) -> None:
    """Stats globales : pourcentage par section, lab le plus difficile, durée totale."""
    table = Table(
        title="[bold]Statistiques[/bold]", show_header=True, header_style="dim",
    )
    table.add_column("Section")
    table.add_column("Done", justify="center")
    table.add_column("Total", justify="center")
    table.add_column("%", justify="right")

    grand_total = 0
    grand_done = 0
    for section in repo.sections:
        done = sum(
            1 for lab in section.labs
            if (run := runs_by_lab.get(lab.path)) is not None and run["status"] == "completed"
        )
        total = len(section.labs)
        pct = 100 * done // max(total, 1)
        style = "green" if pct == 100 else ("yellow" if pct > 0 else "dim")
        table.add_row(
            section.title,
            f"[{style}]{done}[/{style}]",
            str(total),
            f"[{style}]{pct} %[/{style}]",
        )
        grand_total += total
        grand_done += done

    pct_global = 100 * grand_done // max(grand_total, 1)
    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{grand_done}[/bold]",
        f"[bold]{grand_total}[/bold]",
        f"[bold]{pct_global} %[/bold]",
    )
    console.print(table)
