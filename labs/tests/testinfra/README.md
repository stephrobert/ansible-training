# Lab 66 — Molecule + testinfra

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Molecule installé (cf. [lab 62](../62-roles-molecule-introduction/))
> + `pipx inject molecule pytest-testinfra`.

## 🧠 Rappel

🔗 [**Tests Molecule avec testinfra**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/molecule-testinfra/)

Le `verifier: ansible` (lab 62-65) écrit les assertions en **YAML**, ce qui
est OK mais limité. Le `verifier: testinfra` les écrit en **Python** :

| Approche | Forme | Force |
| --- | --- | --- |
| `verifier: ansible` | YAML + `ansible.builtin.assert` | Simple, pas de dépendance Python |
| `verifier: testinfra` | Python + `pytest-testinfra` | Riche, idiomatique, fixtures, paramétrage |

testinfra fournit une **API Python idiomatique** :

```python
def test_nginx_running(host):
    assert host.package("nginx").is_installed
    assert host.service("nginx").is_running
    assert host.socket("tcp://0.0.0.0:80").is_listening
    assert host.file("/etc/nginx/nginx.conf").exists
```

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Configurer Molecule pour utiliser **`verifier: testinfra`**.
2. Écrire des tests Python avec la fixture **`host`** de testinfra.
3. Utiliser les **inspecteurs** : `host.package`, `host.service`,
   `host.file`, `host.socket`, `host.user`, `host.group`, `host.process`.
4. Paramétrer un test avec **`@pytest.mark.parametrize`** (équivalent
   `loop` Ansible).
5. Choisir entre `verifier: ansible` (rapide) et `verifier: testinfra`
   (puissant).

## 🔧 Préparation

```bash
pipx inject molecule pytest-testinfra
pipx inject molecule pytest
```

## ⚙️ Arborescence

```text
labs/tests/testinfra/
├── README.md
├── Makefile
├── roles/
│   └── webserver/
└── molecule/
    └── default/
        ├── molecule.yml          ← verifier: testinfra
        ├── converge.yml
        └── tests/
            └── test_webserver.py ← assertions Python (≥4)
```

## 📚 Exercice 1 — `molecule.yml` avec `verifier: testinfra`

```yaml
verifier:
  name: testinfra
  options:
    v: 1                           # verbose
```

🔍 **Observation** : pas de `verify.yml` — les tests sont en Python dans
`molecule/default/tests/`.

## 📚 Exercice 2 — Premier test testinfra

```python
# molecule/default/tests/test_webserver.py
import pytest


def test_nginx_installed(host):
    assert host.package("nginx").is_installed


def test_nginx_running(host):
    svc = host.service("nginx")
    assert svc.is_running
    assert svc.is_enabled


def test_port_80_listening(host):
    sock = host.socket("tcp://0.0.0.0:80")
    assert sock.is_listening


def test_nginx_conf_owned_by_root(host):
    f = host.file("/etc/nginx/nginx.conf")
    assert f.exists
    assert f.user == "root"
    assert f.mode == 0o644
```

🔍 **Observation** : la fixture **`host`** est injectée automatiquement
par pytest-testinfra. Elle représente l'instance Molecule.

## 📚 Exercice 3 — Inspecteurs avancés

```python
def test_nginx_user_exists(host):
    u = host.user("nginx")
    assert u.exists
    assert u.shell in ("/sbin/nologin", "/usr/sbin/nologin")


def test_no_default_index_page(host):
    """L'apache par défaut ne doit plus être là."""
    cmd = host.run("curl -s http://localhost")
    assert "Welcome to nginx" not in cmd.stdout


@pytest.mark.parametrize("port", [80, 443])
def test_ports_listening(host, port):
    """Test paramétré : 80 et 443 doivent être ouverts."""
    sock = host.socket(f"tcp://0.0.0.0:{port}")
    assert sock.is_listening
```

## 📚 Exercice 4 — Lancer

```bash
cd labs/tests/testinfra
molecule test
```

🔍 La phase `verify` lance maintenant les tests Python.

## 🔍 Observations à noter

- **`verifier: testinfra`** = puissance Python (fixtures, paramétrage,
  héritage). À privilégier pour des tests complexes.
- **`verifier: ansible`** = simplicité YAML. Bon pour des assertions de
  base. N'a pas besoin d'env Python supplémentaire.
- **Inspecteurs testinfra** : `host.package`, `host.service`, `host.file`,
  `host.socket`, `host.user`, `host.group`, `host.process`,
  `host.command`, `host.run`, `host.system_info`. Couvre 95 % des
  besoins.
- **Le helper `lab_host`** que ce repo utilise pour les challenges est
  basé sur testinfra — vous le connaissez déjà.

## 🤔 Questions de réflexion

1. Comment adapter votre solution si la cible passait de **1 host** à un
   parc de **50 serveurs** ? Quels paramètres (`forks`, `serial`, `strategy`)
   faudrait-il ajuster pour conserver des temps d'exécution acceptables ?

2. Quels modules Ansible alternatifs auriez-vous pu utiliser pour atteindre
   le même résultat ? Quels sont leurs trade-offs (idempotence garantie,
   performance, dépendances de collection externe) ?

3. Si une étape du playbook échoue en cours d'exécution, quel est l'impact
   sur les hôtes déjà traités ? Comment rendre le scénario reprenable
   (`block/rescue/always`, `--start-at-task`, `serial`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`host.iptables`** : valider des règles netfilter spécifiques.
- **`host.mount_point`** : valider des montages NFS/iSCSI.
- **`host.docker(name)`** : si l'instance fait tourner Docker.
- **Markers pytest** : skip selon OS (`@pytest.mark.skipif(host.system_info.distribution == 'debian'`).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/tests/testinfra/
```
