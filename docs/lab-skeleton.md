# Squelette d'un lab unitaire

Chaque page de la formation (chaque sous-dossier de `labs/`) doit suivre cette structure et ce contrat. Cela permet à `make test-all` d'agréger tous les labs sans intervention humaine.

## Arborescence

```
labs/<chemin-de-la-page>/
├── README.md                      ← brève description + lien vers la page de la formation
├── Makefile                       ← cibles standard : setup / run / verify / clean
├── playbook.yml                   ← code Ansible de l'exemple
├── inventory.yml                  ← (optionnel) inventaire spécifique si différent du global
├── roles/                         ← (optionnel) si rôles ad hoc
├── group_vars/                    ← (optionnel) si variables ad hoc
├── files/                         ← (optionnel) ressources copiées par le playbook
├── templates/                     ← (optionnel) templates Jinja2
├── expected-output.txt            ← sortie de référence (générée par `make run` au premier passage)
└── challenge/
    ├── README.md                  ← consigne du challenge final (variante autonome de l'exemple)
    └── tests/
        └── test_*.py              ← tests pytest+testinfra qui valident la solution
```

## Squelette du `Makefile`

Quatre cibles obligatoires : `setup`, `run`, `verify`, `clean`. Le wrapper `scripts/test-all.sh` enchaîne `setup → run → verify → clean` dans chaque sous-dossier de `labs/`.

```makefile
# ~/Projets/lab-ansible/labs/<chemin-de-la-page>/Makefile

LAB_ROOT  := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))
INVENTORY := $(LAB_ROOT)/inventory/hosts.yml
PLAYBOOK  := $(CURDIR)/playbook.yml

.PHONY: setup run verify clean help

help:        ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:       ## Restaure l'état initial nécessaire au run (ex : désinstaller un paquet)
	# Exemple :
	# ansible web1 -i $(INVENTORY) -m ansible.builtin.dnf -a "name=nginx state=absent" -b || true

run:         ## Exécute le playbook principal du lab
	cd $(LAB_ROOT) && ansible-playbook $(PLAYBOOK) | tee $(CURDIR)/expected-output.tmp

verify:      ## Tests pytest+testinfra + vérification d'idempotence
	cd $(LAB_ROOT) && pytest -v $(CURDIR)/challenge/tests/
	cd $(LAB_ROOT) && ansible-playbook $(PLAYBOOK) | grep -qE "changed=0\b" \
	    && echo "[lab] OK idempotent" \
	    || (echo "[lab] FAIL — playbook pas idempotent" && exit 1)

clean:       ## Annule les modifications non durables apportées par le run
	@rm -f $(CURDIR)/expected-output.tmp
	# Exemple :
	# ansible web1 -i $(INVENTORY) -m ansible.builtin.dnf -a "name=nginx state=absent" -b || true
```

## Contrat des cibles

| Cible | Doit |
|---|---|
| `setup` | Mettre les managed nodes dans l'état initial attendu par le lab. Souvent **vide** ou idempotent (ex: désinstaller le paquet que le run va installer). |
| `run` | Exécuter le playbook principal. Capturer la sortie dans `expected-output.tmp`. |
| `verify` | (1) Lancer `pytest` sur `challenge/tests/`. (2) Vérifier l'idempotence en relançant le playbook et en attendant `changed=0`. |
| `clean` | Annuler les modifications du run pour ne pas polluer le lab suivant. **Pas** d'effet de bord persistant. |

## Tests pytest + testinfra

[testinfra](https://testinfra.readthedocs.io/) est un plugin pytest qui vérifie l'état d'un système. Il sait se connecter via Ansible et utilise l'inventaire racine du lab.

```python
import pytest
import testinfra

MANAGED_NODES = ["web1.lab", "web2.lab", "db1.lab"]


@pytest.fixture(scope="module", params=MANAGED_NODES)
def host(request):
    return testinfra.get_host(
        f"ansible://{request.param}?ansible_inventory=inventory/hosts.yml"
    )


def test_nginx_running(host):
    assert host.package("nginx").is_installed
    assert host.service("nginx").is_running
    assert host.socket("tcp://0.0.0.0:80").is_listening
```

Lancement :

```bash
pytest -v labs/<chemin>/challenge/tests/
```

## Workflow Claude Code (rappel roadmap §9.2 et §12.5)

Pour chaque page de la formation, dans l'ordre :

1. Créer le dossier `labs/<chemin-de-la-page>/`.
2. Y poser le `Makefile` standard (copier-coller du squelette ci-dessus).
3. Rédiger `playbook.yml` (et ses templates/files si besoin).
4. `make setup run` → capturer `expected-output.tmp` dans `expected-output.txt`.
5. Rédiger `challenge/tests/test_*.py` qui valide l'état post-run.
6. `make verify` doit passer (tests verts + idempotence).
7. `make clean` doit ramener le lab à l'état initial.
8. Rédiger la page Markdown de la formation en intégrant `playbook.yml` et l'extrait pertinent de `expected-output.txt`.
9. Commiter (`lab(<section>/<page>): <description>`).

Aucune page ne quitte le repo sans que `pytest` + idempotence soient verts.
