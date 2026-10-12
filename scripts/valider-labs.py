#!/usr/bin/env python3
"""Éprouve chaque lab dans les DEUX sens, par dsoxlab, et écrit son verdict.

Pourquoi ce script existe
-------------------------
`scripts/test-all.sh` rejoue la solution de référence contre les tests de
chaque lab, par la fixture `_apply_lab_state` du `conftest.py`. Cela prouve
exactement une chose : **la solution passe les tests**.

Cela ne prouve pas l'autre moitié, **les tests échouent avant le travail**. Un
lab dont les tests sont verts sur l'état de départ ne mesure rien, et rien dans
le fichier ne le laisse deviner. Les catalogues Kubernetes et Linux en ont
trouvé ainsi plusieurs, dont un qui rendait 50/100 sans qu'on ait touché à quoi
que ce soit. Sans relevé, les 113 labs de ce dépôt s'affichaient « non
attestés » sur le site.

Ce que le script fait, et rien de plus
--------------------------------------
Il **enchaîne les commandes dsoxlab**, il ne les réimplémente pas. Pour chaque
lab :

    dsoxlab clean <id>     on part d'un état connu
    (ses VM reviennent à leur base figée : snapshot_reset du conftest.py)
    dsoxlab run   <id>     l'état de départ est posé (setup.yaml)
    dsoxlab check <id>     DOIT rendre 0 : le travail n'est pas fait
                           (.vault-pass écarté : voir plus bas)
    (la solution de référence est jouée par la fixture du conftest.py)
    dsoxlab check <id>     DOIT rendre 100, tous les tests passés
    dsoxlab clean <id>     et il ne doit rien rester

Le verdict va dans `validation-labs.json`, versionné, avec la date de SON
rejeu : c'est la trace qui distingue « livrable » de « validé ».

Deux adaptations propres à ce dépôt
-----------------------------------
**Le premier check se joue sans `.vault-pass`.** Le `conftest.py` retombe sur la
solution de référence chiffrée dès que `.vault-pass` est présent :
`assert_idempotent` (85 labs) REJOUE alors la référence sur l'état de départ,
`lab_solution_text` et `lab_script` la lisent ou l'exécutent. Sur le poste du
formateur, un premier check noterait donc la référence, pas l'absence de
travail. L'apprenant, lui, n'a jamais `.vault-pass` : ces tests skippent chez
lui. Le script reproduit sa situation en écartant `.vault-pass` dans le
répertoire `.git/` (jamais suivi, même système de fichiers, donc un simple
renommage) le temps de ce seul check, et le remet en place dans tous les cas,
y compris sur SIGTERM. Un `.vault-pass` resté écarté par un arrêt brutal
(SIGKILL) est remis en place au lancement suivant.

**La solution est jouée par le conftest, pas recopiée.** La fixture
`_apply_lab_state` sait déjà poser la référence : `setup.yaml`, puis
`ansible-playbook --vault-password-file .vault-pass solution/<lab>/solution.yml`
avec les arguments, inventaires et chemins de rôles propres au lab
(`_EXTRA_ARGS`, `_INVENTORY_LABS`, `_EXTRA_ENV`), ou le `solution.sh` posé le
temps du module pour un lab shell. On lance donc la suite du lab SANS
`LAB_NO_REPLAY`, et avec `DSOXLAB_SNAPSHOT_ISOLATION=0` pour que la fixture ne
défasse pas l'état posé par `dsoxlab run` : la solution s'applique là où
l'apprenant l'appliquerait. Rien n'atterrit en clair dans `challenge/`.

Ce que le script surveille en plus
----------------------------------
**Les traces.** Les sections `molecule/` et `ee/` créent des conteneurs ; un
conteneur orphelin fait tomber le lab suivant sans parler de sa cause. Le
script photographie les conteneurs Docker et Podman avant et après, et un lab
qui en laisse est ROUGE. Il compare aussi les fichiers du répertoire du lab :
un fichier versionné modifié, ou une solution laissée dans `challenge/` (que
l'apprenant lirait, et que le check suivant noterait comme son travail), rend
le lab ROUGE ; les autres fichiers non suivis sont seulement nommés.

**Le travail en cours.** Un `challenge/solution.yml` ou `challenge/solution.sh`
présent AVANT le cycle est le travail de quelqu'un : le conftest le jouerait à
la place de la référence, et le verdict ne porterait plus sur elle. Le script
refuse alors de jouer ces labs, et ne touche pas au fichier.

Ce qu'il ne peut pas faire
--------------------------
Il ne juge pas la JUSTESSE d'un lab : un lab peut rendre 0 puis 100 en ne
mesurant rien d'intéressant. Il exige l'infrastructure debout et les bases de
snapshot figées (`mise run provision`, puis `mise run rebase`) : sans elles,
chaque lab VM sort ROUGE pour « isolation impossible », ce qui est voulu.

Usage (depuis la racine du dépôt, avec la chaîne Ansible de mise.toml) :
    mise exec -- python3 scripts/valider-labs.py                  # tout le catalogue
    mise exec -- python3 scripts/valider-labs.py --lab <id> [--lab <id> ...]
    mise exec -- python3 scripts/valider-labs.py --section vault
    python3 scripts/valider-labs.py --check     # ne rejoue rien ; échoue si un lab est ROUGE
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lecture_yaml import YamlIllisible, lire_yaml

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
SOLUTIONS = RACINE / "solution"
VERDICTS = RACINE / "validation-labs.json"
VAULT = RACINE / ".vault-pass"
# Là où `.vault-pass` attend pendant le premier check : dans `.git/`, que git
# ne suit jamais, sur le même système de fichiers (renommage atomique).
CACHETTE = RACINE / ".git" / "valider-labs.vault-pass"

# `dsoxlab check` affiche « Score : 87 / 100 pts » ; on lit le premier nombre.
SCORE = re.compile(r"Score\s*:\s*(\d+)\s*/\s*100")
TESTS = re.compile(r"Tests\s*:\s*[^\d]*(\d+)/(\d+)")

# Un lab qui skippe sans score n'est ni validé ni rouge : il n'a pas pu être joué.
MARQUES_DE_SKIP = ("skipped", "SKIPPED", "Lab non joué")

# Quand la solution ne peut pas être posée, la fixture `_apply_lab_state` lève
# (`_run` : « Commande échouée ») et pytest le rapporte en erreur de SETUP. Un
# test qui échoue, lui, sort en FAILED : c'est au check suivant d'en juger.
ECHEC_DE_POSE = re.compile(r"ERROR at setup of")

# Le travail de l'apprenant, que le conftest jouerait à la place de la référence.
TRAVAIL_APPRENANT = ("challenge/solution.yml", "challenge/solution.sh")

# Bruit d'exécution, sans rapport avec le lab.
BRUIT = ("__pycache__/", ".pytest_cache/")


class IsolationEteinte(RuntimeError):
    """Les VM du lab n'ont pas pu revenir à leur base : le verdict ne vaudrait rien."""


@dataclass
class Verdict:
    """Ce qu'on a mesuré d'un lab, et ce qui permet d'en juger."""

    id: str
    chemin: str
    verdict: str = "INCONNU"
    score_avant: int | None = None
    score_apres: int | None = None
    tests: str | None = None
    duree_s: float = 0.0
    traces: list[str] = field(default_factory=list)
    pourquoi: str = ""


# ── Commandes ────────────────────────────────────────────────────────────────


def _dsoxlab(*args: str, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, LAB_HOME=str(RACINE))
    return subprocess.run(
        ["dsoxlab", *args],
        cwd=RACINE,
        env=env,
        input="y\n",
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _score(sortie: str) -> int | None:
    trouve = SCORE.search(sortie)
    return int(trouve.group(1)) if trouve else None


def _tests(sortie: str) -> str | None:
    trouve = TESTS.search(sortie)
    return f"{trouve.group(1)}/{trouve.group(2)}" if trouve else None


def _python_dsoxlab() -> str:
    """Le Python de l'outil dsoxlab : celui qui porte pytest, testinfra et yaml."""
    binaire = shutil.which("dsoxlab")
    if binaire:
        candidat = Path(binaire).resolve().parent / "python"
        if candidat.is_file():
            return str(candidat)
    return sys.executable


# ── Isolation : celle du conftest, pas une copie ─────────────────────────────

# Le conftest importe pytest en tête : on le charge dans le Python de dsoxlab,
# qui l'a, plutôt que d'en recopier 300 lignes ici. Une seule implémentation de
# l'isolation, celle que `test-all.sh` éprouve déjà.
_RESET = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import conftest as c
hotes = c._lab_vm_fqdns(Path(sys.argv[2]))
manques = c.snapshot_reset(hotes) if hotes else []
print(json.dumps({"hotes": hotes, "manques": manques}))
"""


def _ramener_a_la_base(lab: Path) -> list[str]:
    """Ramène les VM du lab à leur base figée ; rend les FQDN réinitialisés.

    Lève IsolationEteinte si une VM n'a pas pu l'être. Pas de repli : un lab
    joué sans isolation note ce qu'ont laissé les labs précédents, et son
    verdict ne vaudrait rien, dans un sens comme dans l'autre.
    """
    proc = subprocess.run(
        [_python_dsoxlab(), "-c", _RESET, str(RACINE), str(lab)],
        cwd=RACINE,
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    lignes = [ligne for ligne in proc.stdout.splitlines() if ligne.startswith("{")]
    if proc.returncode != 0 or not lignes:
        raise IsolationEteinte((proc.stderr or proc.stdout)[-400:].strip())
    bilan = json.loads(lignes[-1])
    if bilan["manques"]:
        raise IsolationEteinte(
            f"pas de base figée pour {', '.join(bilan['manques'])} : "
            "`mise run rebase` après le dernier `dsoxlab provision`"
        )
    return list(bilan["hotes"])


# ── .vault-pass écarté le temps du premier check ─────────────────────────────


def remettre_le_vault() -> None:
    """Remet en place un `.vault-pass` resté écarté (arrêt brutal précédent)."""
    if CACHETTE.exists() and not VAULT.exists():
        CACHETTE.rename(VAULT)
        print("  .vault-pass remis en place (écarté par un arrêt précédent)", file=sys.stderr)


@contextlib.contextmanager
def sans_vault() -> Iterator[None]:
    """Le temps du bloc, le dépôt est vu comme par l'apprenant : sans `.vault-pass`."""
    if CACHETTE.exists():
        raise RuntimeError(
            f"{CACHETTE} existe déjà à côté de {VAULT.name} : situation ambiguë, "
            "à trancher à la main avant de relancer"
        )
    VAULT.rename(CACHETTE)
    try:
        yield
    finally:
        CACHETTE.rename(VAULT)


def _sigterm_en_sortie(_signum, _frame) -> None:
    # Convertit SIGTERM et SIGHUP en sortie Python : les `finally` tournent, le
    # `.vault-pass` est remis en place et le lab nettoyé.
    raise SystemExit(143)


# ── Solution de référence ────────────────────────────────────────────────────


def _poser_la_solution(lab: Path) -> str | None:
    """Joue la solution de référence par la fixture du conftest.

    Rend un message d'erreur, ou None si la solution a pu être posée. C'est le
    `dsoxlab check` qui suit qui juge, pas ce rejeu.
    """
    rel = lab.relative_to(LABS)
    source = SOLUTIONS / rel
    if not source.is_dir() or not any(p.is_file() for p in source.rglob("*")):
        return f"aucune solution de référence sous solution/{rel.as_posix()}"
    tests = lab / "challenge" / "tests"
    if not tests.is_dir():
        return "aucune suite de tests sous challenge/tests"
    env = {k: v for k, v in os.environ.items() if k not in ("LAB_NO_REPLAY", "VIRTUAL_ENV")}
    env["DSOXLAB_SNAPSHOT_ISOLATION"] = "0"
    proc = subprocess.run(
        [_python_dsoxlab(), "-m", "pytest", str(tests), "-q", "-p", "no:cacheprovider", "--no-header"],
        cwd=RACINE,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    sortie = proc.stdout + proc.stderr
    if ECHEC_DE_POSE.search(sortie):
        return f"la solution n'a pas pu être posée : {sortie[-400:]}"
    return None


# ── Traces ───────────────────────────────────────────────────────────────────


def _conteneurs() -> set[str]:
    """Les conteneurs Docker et Podman présents, pour comparer avant et après."""
    noms: set[str] = set()
    for moteur in ("docker", "podman"):
        if not shutil.which(moteur):
            continue
        proc = subprocess.run(
            [moteur, "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        noms |= {f"{moteur}:{n.strip()}" for n in proc.stdout.splitlines() if n.strip()}
    return noms


def _git(*args: str) -> list[str]:
    proc = subprocess.run(
        ["git", *args], cwd=RACINE, capture_output=True, text=True, check=False
    )
    return [ligne for ligne in proc.stdout.splitlines() if ligne.strip()]


def _etat_fichiers(lab: Path) -> tuple[set[str], set[str]]:
    """(fichiers versionnés modifiés, fichiers non suivis ou ignorés) du lab."""
    rel = lab.relative_to(RACINE).as_posix()
    modifies = set(_git("diff", "--name-only", "HEAD", "--", rel))
    hors_suivi = set(_git("ls-files", "--others", "--exclude-standard", "--", rel))
    hors_suivi |= set(_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", rel))
    return modifies, {f for f in hors_suivi if not any(b in f for b in BRUIT)}


def travail_en_cours(lab: Path) -> list[str]:
    """Les fichiers de travail de l'apprenant présents dans le lab."""
    return [t for t in TRAVAIL_APPRENANT if (lab / t).exists()]


# ── Le cycle ─────────────────────────────────────────────────────────────────


def valider(identifiant: str, lab: Path) -> Verdict:
    """Le cycle complet sur un lab."""
    v = Verdict(id=identifiant, chemin=lab.relative_to(LABS).as_posix())
    debut = time.monotonic()
    conteneurs_avant = _conteneurs()
    modifies_avant, hors_suivi_avant = _etat_fichiers(lab)

    try:
        _dsoxlab("clean", identifiant, timeout=300)

        # Les VM du lab reviennent à leur base figée AVANT le run : sans cela,
        # le premier check note aussi ce qu'ont laissé les labs précédents.
        try:
            _ramener_a_la_base(lab)
        except IsolationEteinte as erreur:
            v.verdict = "ROUGE"
            v.pourquoi = f"isolation impossible : {erreur}"
            return v

        pose = _dsoxlab("run", identifiant)
        if pose.returncode != 0:
            v.verdict = "ROUGE"
            v.pourquoi = f"`run` a échoué : {(pose.stderr or pose.stdout)[-300:]}"
            return v

        # Sens « 0 » : les tests doivent échouer sur l'état de départ, vus
        # comme par l'apprenant, c'est-à-dire sans accès à la référence.
        with sans_vault():
            premier = _dsoxlab("check", identifiant)
        sortie = premier.stdout + premier.stderr
        v.score_avant = _score(sortie)
        if v.score_avant is None and any(m in sortie for m in MARQUES_DE_SKIP):
            v.verdict = "SKIP"
            v.pourquoi = "le lab se skippe : prérequis absent (outil, service ou compte)"
            return v
        if v.score_avant is None:
            v.verdict = "ROUGE"
            v.pourquoi = f"aucun score lisible au premier check : {sortie[-300:]}"
            return v
        if v.score_avant != 0:
            v.verdict = "ROUGE"
            v.pourquoi = (
                f"le lab rend {v.score_avant}/100 AVANT tout travail. Un test vert "
                "sur l'état de départ n'est pas un test, c'est une hypothèse du "
                "setup."
            )
            return v

        # Sens « 100 » : la solution de référence doit tout passer.
        souci = _poser_la_solution(lab)
        if souci:
            v.verdict = "ROUGE"
            v.pourquoi = souci
            return v

        second = _dsoxlab("check", identifiant)
        sortie = second.stdout + second.stderr
        v.score_apres = _score(sortie)
        v.tests = _tests(sortie)

        # On juge sur les TESTS, pas sur le score : le score porte les indices
        # révélés sur ce poste, le lab n'y est pour rien.
        reussis, total = (v.tests or "0/0").split("/")
        if not total or total == "0":
            v.verdict = "ROUGE"
            v.pourquoi = f"aucun test lisible après la solution : {sortie[-300:]}"
            return v
        if reussis != total:
            v.verdict = "ROUGE"
            v.pourquoi = (
                f"la solution de référence ne passe que {v.tests} tests. Soit "
                "elle est fausse, soit un test exige l'impossible."
            )
            return v

        v.verdict = "VALIDE"

    except subprocess.TimeoutExpired as erreur:
        v.verdict = "ROUGE"
        v.pourquoi = f"délai dépassé : {erreur}"
    finally:
        fin = _dsoxlab("clean", identifiant, timeout=300)
        v.duree_s = round(time.monotonic() - debut, 1)
        _juger_les_traces(v, lab, fin, conteneurs_avant, modifies_avant, hors_suivi_avant)

    return v


def _juger_les_traces(
    v: Verdict,
    lab: Path,
    fin: subprocess.CompletedProcess[str],
    conteneurs_avant: set[str],
    modifies_avant: set[str],
    hors_suivi_avant: set[str],
) -> None:
    """Ce que le lab a laissé derrière lui, et ce qui en fait un lab ROUGE."""
    # Les conteneurs préfixés `dsoxlab-` sont ceux que l'outil gère et arrête
    # avec la session : les compter accuserait le lab du travail de l'outil.
    laisses = sorted(
        c for c in _conteneurs() - conteneurs_avant if not c.split(":", 1)[-1].startswith("dsoxlab-")
    )
    modifies, hors_suivi = _etat_fichiers(lab)
    touches = sorted(modifies - modifies_avant)
    nouveaux = sorted(hors_suivi - hors_suivi_avant)
    racine_lab = lab.relative_to(RACINE).as_posix()
    solutions_laissees = [f for f in nouveaux if f in {f"{racine_lab}/{t}" for t in TRAVAIL_APPRENANT}]

    v.traces = [*laisses, *(f"modifié : {f}" for f in touches), *(f"fichier : {f}" for f in nouveaux)]
    if v.verdict != "VALIDE":
        return
    if fin.returncode != 0:
        v.verdict = "ROUGE"
        v.pourquoi = f"`clean` a échoué : {(fin.stderr or fin.stdout)[-300:]}"
    elif laisses:
        v.verdict = "ROUGE"
        v.pourquoi = (
            f"le lab laisse {len(laisses)} conteneur(s) derrière lui : {laisses}. "
            "C'est le lab suivant qui en paiera le prix."
        )
    elif touches:
        v.verdict = "ROUGE"
        v.pourquoi = f"le rejeu a modifié des fichiers versionnés : {touches}"
    elif solutions_laissees:
        v.verdict = "ROUGE"
        v.pourquoi = (
            f"une solution reste dans challenge/ après clean : {solutions_laissees}. "
            "L'apprenant la lirait, et le check suivant la noterait comme son travail."
        )


# ── Catalogue et relevé ──────────────────────────────────────────────────────


def labs_du_catalogue() -> list[tuple[str, Path]]:
    """[(id, répertoire), ...] pour tout lab porteur d'un lab.yaml."""
    trouves = []
    for contrat in sorted(LABS.rglob("lab.yaml")):
        try:
            donnees = lire_yaml(contrat)
        except YamlIllisible as erreur:
            print(f"  lab illisible, écarté : {erreur}", file=sys.stderr)
            continue
        identifiant = donnees.get("id")
        if identifiant:
            trouves.append((identifiant, contrat.parent))
    return trouves


def selectionner(
    catalogue: list[tuple[str, Path]], labs: list[str] | None, section: str | None
) -> tuple[list[tuple[str, Path]], list[str]]:
    """Les labs retenus, et les ids demandés qui n'existent pas."""
    retenus = catalogue
    inconnus: list[str] = []
    if labs:
        connus = {i for i, _ in catalogue}
        inconnus = [i for i in labs if i not in connus]
        retenus = [(i, p) for i, p in retenus if i in set(labs)]
    if section:
        retenus = [
            (i, p) for i, p in retenus if p.relative_to(LABS).parts[0] == section.strip("/")
        ]
    return retenus, inconnus


def charger_verdicts() -> dict:
    if not VERDICTS.is_file():
        return {}
    try:
        return json.loads(VERDICTS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def version(*commande: str) -> str:
    try:
        proc = subprocess.run(commande, capture_output=True, text=True, check=False)
        return proc.stdout.splitlines()[0].strip() if proc.stdout else "inconnue"
    except (OSError, IndexError):
        return "inconnue"


def ecrire_verdicts(resultats: dict) -> None:
    VERDICTS.write_text(
        json.dumps(
            {
                "genere_le": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ansible-core": version("ansible", "--version"),
                "dsoxlab": version("dsoxlab", "--version"),
                "labs": dict(sorted(resultats.items())),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def verifier(enregistres: dict) -> int:
    """Le mode `--check` : ne rejoue rien, échoue si un verdict est ROUGE."""
    if not enregistres:
        print("aucun verdict enregistré : lancez le script sans --check", file=sys.stderr)
        return 1
    rouges = sorted(i for i, v in enregistres.items() if v.get("verdict") == "ROUGE")
    if rouges:
        print(f"{len(rouges)} lab(s) ROUGE : {rouges}", file=sys.stderr)
        return 1
    print(f"{len(enregistres)} labs, aucun ROUGE")
    return 0


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Éprouve chaque lab dans les deux sens et écrit son verdict.",
    )
    analyseur.add_argument(
        "--lab", action="append", help="ne jouer que ce lab, par son id (répétable)"
    )
    analyseur.add_argument("--section", help="une section, par son répertoire sous labs/")
    analyseur.add_argument(
        "--check",
        action="store_true",
        help="ne rejoue rien ; échoue si un verdict enregistré est ROUGE",
    )
    arguments = analyseur.parse_args(argv)

    if arguments.check:
        return verifier(charger_verdicts().get("labs", {}))

    remettre_le_vault()
    if not VAULT.is_file():
        print(".vault-pass absent : les solutions ne peuvent pas être déchiffrées.", file=sys.stderr)
        return 1
    manquants = [o for o in ("dsoxlab", "ansible-playbook") if not shutil.which(o)]
    if manquants:
        print(
            f"introuvable(s) : {', '.join(manquants)}. Lancez le script par "
            "`mise exec -- python3 scripts/valider-labs.py`.",
            file=sys.stderr,
        )
        return 1

    a_jouer, inconnus = selectionner(labs_du_catalogue(), arguments.lab, arguments.section)
    if inconnus:
        print(f"lab(s) inconnu(s) du catalogue : {inconnus}", file=sys.stderr)
        return 1
    if not a_jouer:
        print("aucun lab à jouer avec ces critères", file=sys.stderr)
        return 1

    occupes = {i: travail_en_cours(p) for i, p in a_jouer if travail_en_cours(p)}
    if occupes:
        print(
            "travail en cours dans ces labs, que le conftest jouerait à la place "
            "de la référence ; rien n'est joué, rien n'est touché :",
            file=sys.stderr,
        )
        for i, fichiers in occupes.items():
            print(f"  {i} : {', '.join(fichiers)}", file=sys.stderr)
        return 1

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _sigterm_en_sortie)

    print(f"{len(a_jouer)} lab(s) à éprouver dans les deux sens\n")

    resultats = charger_verdicts().get("labs", {})
    for rang, (identifiant, lab) in enumerate(a_jouer, start=1):
        print(f"[{rang}/{len(a_jouer)}] {identifiant} ... ", end="", flush=True)
        v = valider(identifiant, lab)
        # Chaque lab porte la date de SON rejeu : `genere_le` ne date que la
        # campagne, et un lab rejoué à l'identique serait sinon indiscernable
        # d'une entrée ancienne recopiée.
        resultats[identifiant] = asdict(v) | {"date": time.strftime("%Y-%m-%d")}
        detail = f"{v.score_avant} -> {v.score_apres}" if v.score_avant is not None else ""
        print(f"{v.verdict} {detail} ({v.duree_s}s)")
        if v.pourquoi:
            print(f"      {v.pourquoi}")
        # Au fil de l'eau : une campagne interrompue garde ce qu'elle a mesuré.
        ecrire_verdicts(resultats)

    comptes: dict[str, int] = {}
    for v in resultats.values():
        comptes[v["verdict"]] = comptes.get(v["verdict"], 0) + 1
    print("\n" + ", ".join(f"{n} {etat}" for etat, n in sorted(comptes.items())))
    print(f"verdicts écrits dans {VERDICTS.relative_to(RACINE)}")

    return 1 if comptes.get("ROUGE") else 0


if __name__ == "__main__":
    raise SystemExit(main())
