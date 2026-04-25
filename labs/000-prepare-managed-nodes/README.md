# Lab 000 — Préparer les managed nodes

Ce lab est joué **automatiquement** à la fin de `make provision`. Il prépare les 3 managed nodes (`web1`, `web2`, `db1`) pour qu'ils soient utilisables par tous les playbooks de la formation.

---

## 🧠 Rappel et lecture recommandée

🔗 [**Préparer les nœuds gérés Ansible : Python, SSH, sudo, firewall**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/preparer-noeuds-geres/)

Cette page explique :

- Les **5 prérequis** d'un managed node (Python 3, SSH par clé, sudo NOPASSWD, firewall, NTP)
- Le pattern **« Ansible se prépare lui-même »** : cloud-init pose le minimum, Ansible converge le reste
- Le **bootstrap via le module `raw`** quand Python 3 n'est pas disponible côté cible

---

> Ce lab n'est pas une page de la formation à proprement parler — c'est un **bootstrap idempotent** qui matérialise le principe **Ansible se prépare lui-même**. Cloud-init ne pose que le minimum (user `ansible` + clé SSH + sudo NOPASSWD). Tout le reste — chrony, paquets utiles, /etc/hosts, SELinux, timezone — est appliqué par ce playbook.

## Ce que fait `playbook.yml`

| Tâche | Module | Effet |
|---|---|---|
| Installer paquets de base | `ansible.builtin.dnf` | `python3-libselinux`, `python3-firewall`, `chrony`, `bash-completion`, `vim-enhanced`, `tar`, `rsync` |
| Démarrer chronyd | `ansible.builtin.systemd` | Synchro horaire active (cohérence des facts entre VMs) |
| Inscrire les hôtes du lab | `ansible.builtin.lineinfile` | `/etc/hosts` contient `web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab` |
| SELinux enforcing | `ansible.posix.selinux` | Mode `Enforcing`, policy `targeted` (cohérent RHCE) |
| Timezone | `community.general.timezone` | `Europe/Paris` |

## Lancer manuellement

Depuis la racine du lab :

```bash
ansible-playbook labs/000-prepare-managed-nodes/playbook.yml
```

ou via le squelette Makefile standard :

```bash
cd labs/000-prepare-managed-nodes/
make run verify clean
```

## Idempotence

Un second `make run` doit afficher `changed=0` sur tous les nodes — c'est la définition d'un playbook propre. Si ce n'est pas le cas, c'est que le playbook réécrit quelque chose à chaque passage (typique : `lineinfile` avec une regexp non ancrée). Voir [`docs/troubleshooting.md`](../../docs/troubleshooting.md).

## Tests

Validation par `pytest + testinfra` dans [`challenge/tests/test_prepare.py`](./challenge/tests/test_prepare.py) — vérifie sur chaque managed node :

- chrony installé + chronyd actif
- paquets `python3-libselinux`, `python3-firewall`, `tar`, `rsync` présents
- `/etc/hosts` contient les 4 entrées
- SELinux en `Enforcing`
- timezone `Europe/Paris`

```bash
pytest -v labs/000-prepare-managed-nodes/challenge/tests/
```

## Pourquoi ce pattern

L'ancien lab [`ansible-training`](https://github.com/stephrobert/ansible-training) plaçait à la fin de chaque TP un challenge auto-validé par tests `pytest + testinfra`. Ce pattern est repris ici comme **squelette de référence** pour tous les labs unitaires de la formation. Voir [`docs/lab-skeleton.md`](../../docs/lab-skeleton.md) pour la convention.
