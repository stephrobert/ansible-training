# Standardiser la boîte à outils et sortir telnet du serveur

## La situation

Deux sujets sont arrivés sur votre bureau le même matin. L'équipe d'astreinte
en a assez de trouver **web1.lab** sans éditeur digne de ce nom ni complétion
shell, et le scan de sécurité a signalé le client `telnet`, dont le protocole en
clair n'a rien à faire sur un serveur en 2026. Même play, deux sens opposés :
installer ce qui manque, retirer ce qui ne devrait pas être là. Et comme le parc
Debian arrive au trimestre prochain, le playbook ne doit pas figer le
gestionnaire de paquets RHEL.

Votre mission :

1. Depuis **control-node.lab**, aligner **web1.lab** sur la boîte à outils
   standard (éditeur, complétion shell, vue arborescente) en **une seule
   transaction**, pas une tâche par paquet.
2. Retirer **`telnet`**, et faire prouver l'absence par la base de paquets, pas
   par une commande qui se trouve manquante.
3. Rester **agnostique de la distribution** : le même playbook doit survivre à
   l'arrivée des nœuds Debian sans réécriture vers `apt`.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/

## 🎯 Challenge — Module `package:` (multi-paquets, agnostique de distrib)

### ✅ Objectif

Sur **web1.lab**, gérer 4 paquets **avec un seul module** :

| Paquet | État souhaité |
| --- | --- |
| `vim-enhanced` | `present` |
| `bash-completion` | `present` |
| `tree` | `present` |
| `telnet` | `absent` (protocole en clair, dangereux) |

Utiliser **`ansible.builtin.package`** plutôt que `dnf`. Ce module est
**agnostique** : il choisit `dnf` sur RHEL/AlmaLinux, `apt` sur
Debian/Ubuntu, etc. Idéal pour un même rôle qui doit tourner sur plusieurs
distributions.

### 🧩 Squelette

```yaml
---
- name: Challenge - module package
  hosts: ???
  become: ???

  tasks:
    - name: Installer les paquets utiles (3 paquets en une transaction)
      ansible.builtin.package:
        name:
          - ???
          - ???
          - ???
        state: ???

    - name: Supprimer telnet (protocole en clair, sécurité)
      ansible.builtin.package:
        name: ???
        state: ???
```

> 💡 **Pièges** :
>
> - **`name:`** accepte une string OU une liste. Une **liste** = une
>   seule transaction (plus rapide, plus atomique). Un `loop:` autour
>   d'une string = N transactions (lent, anti-pattern).
> - **`package` vs `dnf`** : `package` est **agnostique** (RHEL et
>   Debian). Si vous avez besoin d'options spécifiques (`enablerepo`,
>   `disable_gpg_check`), utilisez `dnf` directement.
> - **`state: absent`** vs **`state: removed`** : les deux marchent sur
>   `dnf`, mais `absent` est universel (RHEL, Debian, …). Préférer
>   `absent`.
> - **Test pytest** : utilise `host.package("...")` qui interroge la base
>   RPM/dpkg. Pas besoin de relancer le playbook si vous nettoyez
>   manuellement avec `dnf`.

### 🚀 Lancement

```bash
ansible-playbook labs/modules-paquets/package/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "rpm -q vim-enhanced bash-completion tree"
ansible web1.lab -m ansible.builtin.command -a "rpm -q telnet" || echo "telnet absent (OK)"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-paquets/package/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-paquets-package
```

### 💡 Pour aller plus loin

- **`package` vs `dnf`** : préférez `package` quand le code peut tourner sur
  plusieurs distrib. Préférez `dnf` (ou `apt`) quand vous avez besoin
  d'**options spécifiques** (`enablerepo`, `disable_gpg_check`, etc.) — voir
  lab 37.
- **`package` + liste** : `package` accepte une liste de paquets en `name:` —
  une seule transaction au lieu de N. Plus rapide et plus atomique qu'un
  `loop:`.
- **Lint** :

   ```bash
   ansible-lint labs/modules-paquets/package/challenge/solution.yml
   ```
