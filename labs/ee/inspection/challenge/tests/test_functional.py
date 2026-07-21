"""Tests du lab 85 : inspection comparée de 3 EE.

Le script est livré en squelette et le rapport n'existe pas : ces tests
ne passent que lorsque l'apprenant a écrit inspect.sh, l'a exécuté, et
que le rapport généré contient les faits attendus.

Pytest ne tire pas les images lui-même (pulls de plusieurs Go, réseau) :
il contrôle la syntaxe réelle du script (bash -n), sa sémantique, et le
contenu factuel du rapport produit par l'exécution de l'apprenant.
"""

import re
import subprocess
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
INSPECT = LAB_DIR / "inspect.sh"
REPORT = LAB_DIR / "inspect-output" / "comparison.md"

EES = ("creator-ee", "awx-ee", "community-ee-minimal")


def _code(script):
    """Le CODE du script, commentaires retirés.

    Les tests cherchaient leurs chaînes dans le fichier entier. Or le squelette
    porte son cahier des charges en commentaire, et ce cahier des charges cite
    justement `creator-ee`, `awx-ee`, `podman`, `ansible-navigator` : quatre
    tests sur cinq passaient donc sans qu'une ligne de code soit écrite. Le
    test validait l'énoncé.

    C'est du shell : on ne peut pas en parser la structure comme du YAML, mais
    on peut au moins ne pas prendre un commentaire pour du travail.
    """
    lignes = []
    for ligne in script.read_text().splitlines():
        nue = ligne.split("#", 1)[0]
        if nue.strip():
            lignes.append(nue)
    return "\n".join(lignes)


def test_inspect_script_completed():
    assert INSPECT.is_file(), "inspect.sh manquant"
    assert INSPECT.stat().st_mode & 0o111, "inspect.sh doit être exécutable (chmod +x)"
    content = INSPECT.read_text()
    assert "???" not in content, (
        "inspect.sh contient encore des ??? : complétez le squelette"
    )


def test_inspect_script_valid_bash():
    """bash -n : le script doit être syntaxiquement valide."""
    result = subprocess.run(
        ["bash", "-n", str(INSPECT)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"bash -n rejette inspect.sh :\n{result.stderr}"


def test_inspect_script_covers_three_ees():
    content = _code(INSPECT)
    for ee in EES:
        assert ee in content, (
            f"inspect.sh doit inspecter {ee} : la comparaison porte sur les 3 "
            "EE officiels"
        )


def test_inspect_script_uses_expected_tools():
    content = _code(INSPECT)
    assert "podman" in content, (
        "inspect.sh doit utiliser podman (run --rm, image inspect)"
    )
    assert "ansible-navigator" in content, (
        "inspect.sh doit aussi montrer l'exploration via ansible-navigator"
    )
    assert "comparison.md" in content, (
        "inspect.sh doit générer le rapport inspect-output/comparison.md"
    )


def test_report_generated_with_facts():
    """Le rapport doit exister et contenir des faits, pas des promesses."""
    assert REPORT.is_file(), (
        "inspect-output/comparison.md absent : exécutez ./inspect.sh, c'est "
        "lui qui doit générer le rapport"
    )
    content = REPORT.read_text()
    for ee in EES:
        assert ee in content, f"Le rapport doit couvrir {ee}"
    versions = re.findall(r"\b2\.\d{2}\.\d+\b", content)
    assert len(versions) >= 2, (
        "Le rapport doit citer les versions d'ansible-core CONSTATÉES dans "
        "les images (format 2.XX.Y), issues de podman run ... ansible --version"
    )
    assert content.count("|") >= 12, (
        "Le rapport doit être un tableau Markdown (| image | version | taille |)"
    )
