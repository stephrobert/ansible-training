# Lab decouvrir/installation-ansible

Vérifie que votre installation d'Ansible est fonctionnelle et expose les bons composants.

Pas de playbook côté managed nodes — c'est un lab **local** sur votre control node.

## Lancer la vérification

```bash
make verify
```

## Ce que ça contrôle

- `ansible --version` retourne **core ≥ 2.18** (cible RHCE EX294 RHEL 9/10 — 2026).
- `ansible-doc -l` liste **au moins 100 modules** (sanity check, valeur réelle ~10 000 avec les collections communautaires installées).
- Les binaires Ansible standard sont dans le `PATH` : `ansible`, `ansible-playbook`, `ansible-galaxy`, `ansible-doc`, `ansible-vault`, `ansible-config`, `ansible-inventory`.
- Les collections Galaxy installées via le `requirements.yml` du lab sont bien présentes (`ansible.posix`, `community.general`).
