"""L'isolation entre labs ne peut plus s'éteindre en silence (#64).

`scripts/test-all.sh` rendait 58 erreurs et 8 échecs sur 17 labs ; rejoués un
par un, ces mêmes labs passaient tous. Ce n'était pas une régression de contenu
mais l'isolation qui ne tenait pas sur la longueur d'un run.

L'hypothèse principale de l'issue s'est vérifiée par lecture : `snapshot_reset`
faisait un `continue` **muet** quand les bases de snapshot n'existaient pas, et
son retour était **ignoré** par son unique appelant. Le commentaire du conftest
l'assumait — « No-op tant que les bases n'existent pas » — sans mesurer ce que
ce silence coûte : chaque lab note alors l'état laissé par son prédécesseur sur
des VM partagées.

Ce module ne rejoue pas les 58 erreurs : elles demandent un run complet sur
quatre VM. Il tient la règle qui les rend diagnosticables — **une isolation qui
ne s'applique pas le dit et arrête le lab**, au lieu de le laisser mesurer autre
chose que ce qu'il croit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import conftest


def test_snapshot_reset_nomme_les_hotes_manques(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le cœur du défaut : une base absente produisait un `continue` muet.

    Rendre la liste plutôt qu'un booléen n'est pas cosmétique — c'est ce qui
    permet au message d'échec de nommer l'hôte, donc de dire quoi réparer.
    """
    monkeypatch.setattr(conftest, "_domain_disks", lambda f: ["/x/" + f + ".qcow2"])
    monkeypatch.setattr(conftest, "_base_path", lambda d: "/absent/base.qcow2")
    monkeypatch.setattr(conftest, "_mem_save_path", lambda f: "/absent/mem")

    manques = conftest.snapshot_reset(["web1.lab", "db1.lab"])

    assert manques == ["web1.lab", "db1.lab"]


def test_un_hote_sans_domaine_est_signale(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un FQDN sans domaine libvirt n'est pas une isolation réussie.

    Le code le traitait comme les autres `continue` : rien à réinitialiser,
    donc on passe. Mais un lab qui déclare un hôte inexistant tourne sur autre
    chose que ce qu'il croit.
    """
    monkeypatch.setattr(conftest, "_domain_disks", lambda f: [])

    assert conftest.snapshot_reset(["fantome.lab"]) == ["fantome.lab"]


def test_aucun_hote_demande_ne_manque_rien() -> None:
    """L'autre bout : un lab sans hôte VM ne doit rien déclencher."""
    assert conftest.snapshot_reset([]) == []


def test_l_exception_existe_et_porte_un_nom_parlant() -> None:
    """Le message d'échec est la moitié utile du garde-fou.

    Une exception nue laisserait l'utilisateur devant « une erreur », là où il
    lui faut savoir que c'est l'isolation, et quel geste la rétablit.
    """
    assert issubclass(conftest.IsolationEteinte, RuntimeError)


def test_le_conftest_n_ignore_plus_le_retour(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le défaut tenait autant à l'appelant qu'à la fonction.

    `snapshot_reset(...)` était appelée pour son effet de bord, son retour jeté.
    Corriger la fonction sans corriger l'appel n'aurait rien changé.
    """
    source = (RACINE / "conftest.py").read_text(encoding="utf-8")

    assert "manques = snapshot_reset(" in source, (
        "le retour de snapshot_reset doit être lu"
    )
    assert "raise IsolationEteinte(" in source, (
        "une isolation impossible doit arrêter le lab"
    )


def test_l_opt_out_reste_possible() -> None:
    """Assumer explicitement l'absence d'isolation reste permis.

    Un garde-fou sans échappatoire se contourne par des moyens pires — ici, en
    le retirant. La variable rend le choix visible dans la commande.
    """
    source = (RACINE / "conftest.py").read_text(encoding="utf-8")

    assert 'DSOXLAB_SNAPSHOT_ISOLATION") != "0"' in source


def test_le_message_dit_le_geste_de_reprise() -> None:
    """Nommer le problème sans dire quoi faire déplace la charge sur le lecteur."""
    source = (RACINE / "conftest.py").read_text(encoding="utf-8")

    debut = source.index("raise IsolationEteinte(")
    message = source[debut:debut + 700]

    assert "mise run rebase" in message, "le geste qui recrée les bases"
    assert "DSOXLAB_SNAPSHOT_ISOLATION=0" in message, "l'échappatoire assumée"
