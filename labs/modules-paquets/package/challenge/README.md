# 🎯 Challenge — Module `package:` (multi-paquets, agnostique de distrib)

## ✅ Objectif

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

## 🧩 Squelette

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

## 🚀 Lancement

```bash
ansible-playbook labs/modules-paquets/package/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "rpm -q vim-enhanced bash-completion tree"
ansible web1.lab -m ansible.builtin.command -a "rpm -q telnet" || echo "telnet absent (OK)"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-paquets/package/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-paquets/package clean
```

## 💡 Pour aller plus loin

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
