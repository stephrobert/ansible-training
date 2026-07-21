"""Vérifie que le `doc_url` de chaque lab pointe une page qui répond.

`dsoxlab validate-structure` impose qu'un `doc_url` existe et soit en http(s),
mais ne peut pas savoir s'il répond : une page renommée ou déplacée côté site
laisse un lien mort que rien ne signale. L'apprenant, lui, tombe sur un 404 au
moment précis où il cherche le cours.

**Ce module n'est pas collecté par la suite normale** : `testpaths = ["labs"]`
dans `pyproject.toml` limite la collecte aux challenges. C'est voulu, pour deux
raisons : il fait une centaine de requêtes réseau (lent), et il échouerait hors
ligne ou pendant une indisponibilité du site, ce qui n'a rien à voir avec la
justesse des labs.

On le lance explicitement, typiquement après une refonte du site :

    pytest tests/test_doc_urls.py -v

Une page écrite mais pas encore publiée sort logiquement en 404 : dans ce cas,
c'est le déploiement qu'il faut attendre, pas le `doc_url` qu'il faut changer.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urldefrag

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.resolve()
TIMEOUT = 20

# Certains sites refusent une requête sans User-Agent identifiable.
HEADERS = {"User-Agent": "ansible-training-doc-url-check/1.0"}


def _doc_urls() -> dict[str, list[str]]:
    """{url sans ancre: [labs qui la référencent]}.

    Dédupliqué : plusieurs labs peuvent légitimement pointer la même page, et
    la tester dix fois n'apprendrait rien de plus.
    """
    par_url: dict[str, list[str]] = defaultdict(list)
    for lab_yaml in sorted((REPO_ROOT / "labs").rglob("lab.yaml")):
        try:
            data = yaml.safe_load(lab_yaml.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # un lab.yaml illisible est le problème du validator
        if not isinstance(data, dict):
            continue
        url = data.get("doc_url")
        if not url:
            continue
        # L'ancre (#section) n'est pas vérifiable en HTTP : le serveur rend la
        # page entière, le fragment est résolu par le navigateur.
        page, _ = urldefrag(str(url))
        par_url[page].append(str(data.get("id", lab_yaml.parent.name)))
    return dict(par_url)


DOC_URLS = _doc_urls()


def _status(url: str) -> int:
    """Code HTTP, en tentant HEAD puis GET.

    Des hébergeurs statiques répondent 403/405 à HEAD tout en servant la page :
    on retombe alors sur GET plutôt que de crier au lien mort.
    """
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return int(response.status)
        except urllib.error.HTTPError as exc:
            if method == "GET" or exc.code not in (403, 405):
                return int(exc.code)
        except urllib.error.URLError as exc:  # DNS, TLS, réseau coupé
            pytest.skip(f"réseau indisponible pour {url} : {exc.reason}")
    return 0


def test_le_catalogue_declare_des_doc_url() -> None:
    """Garde-fou : sans ça, une regression de _doc_urls() rendrait la suite verte à vide."""
    assert DOC_URLS, "aucun doc_url trouvé sous labs/ : le parsing est cassé"


@pytest.mark.parametrize("url", sorted(DOC_URLS), ids=lambda u: u.rsplit("ansible/", 1)[-1])
def test_doc_url_repond(url: str) -> None:
    code = _status(url)
    labs = ", ".join(sorted(DOC_URLS[url]))

    assert 200 <= code < 400, (
        f"{url} rend HTTP {code}.\n"
        f"Référencée par : {labs}.\n"
        "Soit la page a été renommée ou déplacée côté site et le doc_url doit "
        "suivre, soit elle est écrite mais pas encore publiée, et il faut "
        "attendre le déploiement."
    )
