"""Le validateur de labs juge juste, sans jouer un seul lab.

`scripts/valider-labs.py` éprouve chaque lab dans les deux sens (0 avant le
travail, 100 après la solution de référence). Une campagne complète demande les
quatre VM et plusieurs heures : ce module ne la rejoue pas. Il remplace les
commandes (`dsoxlab`, le reset des VM, le rejeu de la solution, l'inventaire
des conteneurs) par des doublures, et tient les règles qui font la valeur du
verdict :

- un lab qui rend des points AVANT le travail est ROUGE ;
- une solution qui ne passe pas tous les tests est ROUGE ;
- une isolation impossible arrête le lab avant `run` ;
- le premier check se joue SANS `.vault-pass`, qui revient ensuite, y compris
  quand le check lève ;
- un conteneur laissé, un fichier versionné modifié ou une solution restée dans
  `challenge/` rendent le lab ROUGE ;
- chaque verdict porte la date de son rejeu, et `--check` échoue sur un ROUGE.

    pytest tests/test_valider_labs.py -v
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
# Le module partagé, identique dans les douze catalogues.
sys.path.insert(0, str(RACINE / "scripts"))
import verdict_check

SCRIPT = RACINE / "scripts" / "valider-labs.py"


def _charger():
    spec = importlib.util.spec_from_file_location("valider_labs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # Les dataclasses relisent leur module dans sys.modules à la définition.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def vl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Le module, rebranché sur un faux dépôt : rien ne touche au vrai."""
    m = _charger()
    depot = tmp_path / "depot"
    lab = depot / "labs" / "vault" / "introduction"
    (lab / "challenge" / "tests").mkdir(parents=True)
    (lab / "lab.yaml").write_text("id: vault-introduction\ntitle: t\nlevel: l1\n", encoding="utf-8")
    (depot / "labs" / "vault" / "autre").mkdir(parents=True)
    (depot / "labs" / "vault" / "autre" / "lab.yaml").write_text("id: vault-autre\n", encoding="utf-8")
    (depot / "labs" / "roles" / "premier").mkdir(parents=True)
    (depot / "labs" / "roles" / "premier" / "lab.yaml").write_text("id: roles-premier\n", encoding="utf-8")
    (depot / "solution" / "vault" / "introduction").mkdir(parents=True)
    (depot / "solution" / "vault" / "introduction" / "solution.yml").write_text(
        "$ANSIBLE_VAULT;1.1;AES256\n", encoding="utf-8"
    )
    (depot / ".git").mkdir()
    (depot / ".vault-pass").write_text("secret-de-test\n", encoding="utf-8")

    monkeypatch.setattr(m, "RACINE", depot)
    monkeypatch.setattr(m, "LABS", depot / "labs")
    monkeypatch.setattr(m, "SOLUTIONS", depot / "solution")
    monkeypatch.setattr(m, "VERDICTS", depot / "validation-labs.json")
    monkeypatch.setattr(m, "VAULT", depot / ".vault-pass")
    monkeypatch.setattr(m, "CACHETTE", depot / ".git" / "valider-labs.vault-pass")
    monkeypatch.setattr(m, "_conteneurs", lambda: set())
    monkeypatch.setattr(m, "_etat_fichiers", lambda _lab: (set(), set()))
    monkeypatch.setattr(m, "_ramener_a_la_base", lambda _lab: ["db1.lab"])
    monkeypatch.setattr(m, "_poser_la_solution", lambda _lab: None)
    m.LAB = lab
    return m


def _sortie(score: int, reussis: int, total: int, skippes: int = 0) -> str:
    """Le document de `dsoxlab check --json`, tel que le moteur le rend.

    C'est `status` que le script lit, et non `ok` ni `score` : une suite
    entièrement skippée rend `ok: true` et `score: 0`, qui se contredisent.
    """
    mesure = total > skippes
    return json.dumps({
        "schema": 1,
        "check": {
            "ok": reussis == total - skippes,
            "passed": reussis,
            "total": total,
            "skipped": skippes,
            "score": score,
            "max_score": 100,
            "recorded": mesure,
            "status": ("not_measured" if not mesure
                       else "passed" if reussis == total else "failed"),
            "output": f"{reussis} passed, {total - reussis - skippes} failed",
        },
    })


class FausseCLI:
    """Doublure de `dsoxlab` : rend un score par check, note les appels."""

    def __init__(self, vl, checks: list[str], rc_run: int = 0, rc_clean: int = 0):
        self.vl = vl
        self.checks = list(checks)
        self.rc_run = rc_run
        self.rc_clean = rc_clean
        self.appels: list[str] = []
        self.vault_pendant_check: list[bool] = []

    def __call__(self, *args: str, timeout: int = 900):
        self.appels.append(args[0])
        rc, sortie = 0, ""
        if args[0] == "check":
            self.vault_pendant_check.append(self.vl.VAULT.exists())
            sortie = self.checks.pop(0)
        elif args[0] == "run":
            rc = self.rc_run
        elif args[0] == "clean":
            rc = self.rc_clean
        return subprocess.CompletedProcess(["dsoxlab", *args], rc, sortie, "")


def test_un_lab_juste_est_valide(vl, monkeypatch) -> None:
    cli = FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)])
    monkeypatch.setattr(vl, "_dsoxlab", cli)

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "VALIDE", v.pourquoi
    assert (v.score_avant, v.score_apres, v.tests) == (0, 100, "4/4")
    assert cli.appels == ["clean", "run", "check", "check", "clean"]


def test_des_points_avant_le_travail_rendent_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(50, 2, 4)]))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "AVANT tout travail" in v.pourquoi


def test_une_solution_partielle_rend_le_lab_rouge(vl, monkeypatch) -> None:
    """On juge sur les tests : un 100 de score avec 3/4 tests reste ROUGE."""
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 3, 4)]))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "3/4" in v.pourquoi


def test_une_solution_impossible_a_poser_rend_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4)]))
    monkeypatch.setattr(vl, "_poser_la_solution", lambda _lab: "la solution n'a pas pu être posée")

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "posée" in v.pourquoi


def test_une_isolation_impossible_arrete_le_lab_avant_run(vl, monkeypatch) -> None:
    cli = FausseCLI(vl, [])
    monkeypatch.setattr(vl, "_dsoxlab", cli)

    def sans_base(_lab):
        raise vl.IsolationEteinte("pas de base figée pour db1.lab")

    monkeypatch.setattr(vl, "_ramener_a_la_base", sans_base)

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "isolation impossible" in v.pourquoi
    assert "run" not in cli.appels
    assert cli.appels[-1] == "clean"


def test_un_run_en_echec_rend_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [], rc_run=2))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "`run` a échoué" in v.pourquoi


def test_une_suite_entierement_skippee_est_skip(vl, monkeypatch) -> None:
    """Trois tests collectés, aucun joué : rien n'a été mesuré.

    Le moteur rend alors `ok: true` et `score: 0`, qui se contredisent. Lire
    l'un ou l'autre concluait au succès ou à l'échec là où le lab n'avait pas
    tourné : c'est le poste qui n'était pas prêt, pas le lab.
    """
    monkeypatch.setattr(vl, "_dsoxlab",
                        FausseCLI(vl, [_sortie(0, 0, 3, skippes=3)]))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "SKIP"
    assert "tous skippé" in v.pourquoi, v.pourquoi


def test_le_premier_check_se_joue_sans_vault_et_le_second_avec(vl, monkeypatch) -> None:
    """Le cœur de l'adaptation Ansible : l'apprenant n'a jamais `.vault-pass`."""
    cli = FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)])
    monkeypatch.setattr(vl, "_dsoxlab", cli)

    vl.valider("vault-introduction", vl.LAB)

    assert cli.vault_pendant_check == [False, True]
    assert vl.VAULT.read_text(encoding="utf-8") == "secret-de-test\n"
    assert not vl.CACHETTE.exists()


def test_le_vault_revient_meme_si_le_check_leve(vl, monkeypatch) -> None:
    def check_qui_leve(*args, timeout=900):
        if args[0] == "check":
            raise subprocess.TimeoutExpired(["dsoxlab", *args], timeout)
        return subprocess.CompletedProcess(["dsoxlab", *args], 0, "", "")

    monkeypatch.setattr(vl, "_dsoxlab", check_qui_leve)

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "délai dépassé" in v.pourquoi
    assert vl.VAULT.exists() and not vl.CACHETTE.exists()


def test_un_vault_reste_ecarte_est_remis_en_place(vl) -> None:
    vl.VAULT.rename(vl.CACHETTE)

    vl.remettre_le_vault()

    assert vl.VAULT.exists() and not vl.CACHETTE.exists()


def test_vault_et_cachette_ensemble_sont_refuses(vl) -> None:
    vl.CACHETTE.write_text("autre\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="ambiguë"), vl.sans_vault():
        pass
    assert vl.VAULT.read_text(encoding="utf-8") == "secret-de-test\n"


def test_un_conteneur_laisse_rend_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)]))
    etats = iter([set(), {"podman:molecule-instance", "docker:dsoxlab-service"}])
    monkeypatch.setattr(vl, "_conteneurs", lambda: next(etats))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert v.traces == ["podman:molecule-instance"]


def test_un_fichier_versionne_modifie_rend_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)]))
    etats = iter([(set(), set()), ({"labs/vault/introduction/challenge/lab.yml"}, set())])
    monkeypatch.setattr(vl, "_etat_fichiers", lambda _lab: next(etats))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "fichiers versionnés" in v.pourquoi


def test_une_solution_restee_dans_challenge_rend_le_lab_rouge(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)]))
    reste = "labs/vault/introduction/challenge/solution.sh"
    etats = iter([(set(), set()), (set(), {reste})])
    monkeypatch.setattr(vl, "_etat_fichiers", lambda _lab: next(etats))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert reste in v.pourquoi


def test_un_autre_fichier_laisse_est_seulement_nomme(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl, "_dsoxlab", FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)]))
    etats = iter([(set(), set()), (set(), {"labs/vault/introduction/challenge/build/x.tar.gz"})])
    monkeypatch.setattr(vl, "_etat_fichiers", lambda _lab: next(etats))

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "VALIDE"
    assert v.traces == ["fichier : labs/vault/introduction/challenge/build/x.tar.gz"]


def test_un_clean_final_en_echec_rend_le_lab_rouge(vl, monkeypatch) -> None:
    cli = FausseCLI(vl, [_sortie(0, 0, 4), _sortie(100, 4, 4)])
    monkeypatch.setattr(vl, "_dsoxlab", cli)
    cli.rc_clean = 2

    v = vl.valider("vault-introduction", vl.LAB)

    assert v.verdict == "ROUGE"
    assert "`clean` a échoué" in v.pourquoi


def test_lab_repetable_section_et_id_inconnu(vl) -> None:
    catalogue = vl.labs_du_catalogue()
    assert {i for i, _ in catalogue} == {"vault-introduction", "vault-autre", "roles-premier"}

    retenus, inconnus = vl.selectionner(catalogue, ["vault-autre", "roles-premier"], None)
    assert sorted(i for i, _ in retenus) == ["roles-premier", "vault-autre"]
    assert inconnus == []

    retenus, _ = vl.selectionner(catalogue, None, "vault")
    assert sorted(i for i, _ in retenus) == ["vault-autre", "vault-introduction"]

    _, inconnus = vl.selectionner(catalogue, ["vault-fantome"], None)
    assert inconnus == ["vault-fantome"]


def test_un_travail_en_cours_bloque_la_campagne_sans_etre_touche(vl, monkeypatch, capsys) -> None:
    travail = vl.LAB / "challenge" / "solution.yml"
    travail.write_text("- hosts: lab_target\n", encoding="utf-8")
    monkeypatch.setattr(vl.shutil, "which", lambda _o: "/usr/bin/x")
    monkeypatch.setattr(vl, "valider", lambda *_: pytest.fail("aucun lab ne doit être joué"))

    assert vl.main(["--lab", "vault-introduction"]) == 1
    assert "vault-introduction" in capsys.readouterr().err
    assert travail.read_text(encoding="utf-8") == "- hosts: lab_target\n"


def test_chaque_verdict_porte_la_date_de_son_rejeu(vl, monkeypatch) -> None:
    monkeypatch.setattr(vl.shutil, "which", lambda _o: "/usr/bin/x")
    monkeypatch.setattr(vl, "version", lambda *_: "x 1.0")
    monkeypatch.setattr(vl.signal, "signal", lambda *_: None)
    monkeypatch.setattr(
        vl, "valider", lambda i, p: vl.Verdict(id=i, chemin="vault/introduction", verdict="VALIDE")
    )
    vl.VERDICTS.write_text(
        json.dumps({"labs": {"vault-autre": {"verdict": "VALIDE", "date": "2026-01-01"}}}),
        encoding="utf-8",
    )

    assert vl.main(["--lab", "vault-introduction"]) == 0

    releve = json.loads(vl.VERDICTS.read_text(encoding="utf-8"))
    assert releve["labs"]["vault-introduction"]["date"] == time.strftime("%Y-%m-%d")
    assert releve["labs"]["vault-autre"]["date"] == "2026-01-01"
    assert {"genere_le", "ansible-core", "dsoxlab"} <= releve.keys()


@pytest.mark.parametrize(
    ("labs", "attendu"),
    [
        ({}, 1),
        ({"a": {"verdict": "VALIDE"}, "b": {"verdict": "ROUGE"}}, 1),
        # Un SKIP a son propre code : il ne se répare pas, il se remesure. Le
        # rendre en 0 faisait passer pour vert un catalogue dont la moitié
        # n'avait pas pu être jouée.
        ({"a": {"verdict": "VALIDE"}, "b": {"verdict": "SKIP"}}, 10),
        ({"a": {"verdict": "SKIP"}, "b": {"verdict": "ROUGE"}}, 1),
        ({"a": {"verdict": "VALIDE"}}, 0),
    ],
)
def test_le_mode_check(vl, labs: dict, attendu: int) -> None:
    vl.VERDICTS.write_text(json.dumps({"labs": labs}), encoding="utf-8")

    assert vl.main(["--check"]) == attendu


def test_le_verdict_se_lit_dans_le_contrat_et_pas_dans_lencadre(vl) -> None:
    """`status` tranche là où `ok` et `score` se contredisent.

    L'encadré que `dsoxlab check` affiche est de l'interface : il a changé en
    0.4.0 et la regex qui le lisait a cessé de trouver quoi que ce soit. Le
    document `--json` porte un `schema`, c'est un contrat.
    """
    c = verdict_check.lire(_sortie(87, 7, 8))

    assert (c["passed"], c["total"], c["score"]) == (7, 8, 87)
    assert c["status"] == "failed"
    assert verdict_check.a_mesure(c)

    skippe = verdict_check.lire(_sortie(0, 0, 5, skippes=5))

    assert skippe["status"] == "not_measured"
    assert not verdict_check.a_mesure(skippe)
    # La note n'est pas lue quand le moteur ne l'a pas inscrite : un 0 sur une
    # exécution non mesurée n'est pas une note, c'est une absence.
    assert skippe["score"] is None


def test_un_dsoxlab_trop_ancien_arrete_la_campagne(vl) -> None:
    """Un document sans `status` vient d'un outil antérieur à la 0.4.1.

    Se taire ferait reprendre exactement le défaut qu'on corrige, et marquer
    400 labs rouges accuserait les labs d'un défaut d'outil. On s'arrête en
    nommant le geste.
    """
    ancien = json.dumps({"schema": 1, "check": {
        "ok": True, "passed": 0, "total": 5, "score": 0,
    }})

    with pytest.raises(verdict_check.JsonIllisible, match="0.4.1"):
        verdict_check.lire(ancien)


def test_le_reattesteur_du_site_reconnait_le_check() -> None:
    """`reattester-labs.py` cherche la chaîne `"--check"` dans le script."""
    assert '"--check"' in SCRIPT.read_text(encoding="utf-8")
