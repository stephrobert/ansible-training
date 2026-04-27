# 🎯 Challenge — Règles sudo granulaires

## ✅ Objectif

Sur **db1.lab**, créer **3 règles sudo** dans `/etc/sudoers.d/` via le module
`community.general.sudoers`.

## 🧩 Règles à provisionner

| Fichier | User/Groupe | Commandes | Mot de passe ? | RunAs |
| --- | --- | --- | --- | --- |
| `lab-rhce-alice` | user `alice` | `ALL` | **oui** (avec password) | (défaut) |
| `lab-rhce-ops-team` | groupe `ops-team` | `ALL` | non (`NOPASSWD`) | (défaut) |
| `lab-rhce-alice-as-deploy` | user `alice` | `/opt/myapp/bin/deploy.sh` | non | `deploy` |

## 🧩 Pré-requis (étape `users`)

Avant les règles sudo, créez :

- Users : `alice`, `bob`, `deploy`.
- Groupe : `ops-team`.
- `bob` membre du groupe `ops-team` (`groups: ops-team, append: true`).

## 🧩 Indices `community.general.sudoers`

| Option | Effet |
| --- | --- |
| `name:` | Identifiant + **nom du fichier** dans `/etc/sudoers.d/` |
| `user:` | User cible (XOR avec `group:`) |
| `group:` | Groupe cible (XOR avec `user:`) |
| `commands:` | Commandes autorisées (string ou liste) |
| `runas:` | "exécuter en tant que" |
| `nopassword: true` | NOPASSWD (sans mot de passe) |
| `nopassword: false` | Force la saisie du mot de passe (par défaut, c'est `true` — attention) |

> ⚠️ **Piège** : par défaut, `nopassword:` vaut `true`. Pour la règle alice
> qui **doit** demander le mot de passe, vous devez l'expliciter à `false`.

## 🧩 Squelette

```yaml
---
- name: Challenge - règles sudo granulaires
  hosts: db1.lab
  become: true

  tasks:
    - name: Pré-requis users
      ansible.builtin.user:
        name: "{{ item }}"
        state: present
        shell: /bin/bash
      loop: ???

    - name: Pré-requis groupe ops-team
      ansible.builtin.group:
        name: ???
        state: present

    - name: bob membre de ops-team
      ansible.builtin.user:
        name: ???
        groups: ???
        append: ???

    - name: Sudo complet pour alice (avec password)
      community.general.sudoers:
        name: ???
        user: ???
        commands: ???
        nopassword: ???
        state: present

    - name: Sudo complet pour ops-team (NOPASSWD)
      community.general.sudoers:
        name: ???
        group: ???
        commands: ???
        nopassword: ???
        state: present

    - name: alice peut lancer deploy.sh en tant que deploy
      community.general.sudoers:
        name: ???
        user: ???
        runas: ???
        commands: ???
        nopassword: ???
        state: present
```

> 💡 **Pièges** :
>
> - **`nopassword:`** est `true` par défaut sur `community.general.sudoers`.
>   Pour exiger un mot de passe : **`nopassword: false`** explicitement.
>   Erreur classique d'oubli.
> - **`commands:`** accepte une **liste**. Format : chemin absolu de la
>   commande (`/usr/bin/systemctl`), pas juste le nom.
> - **`runas:`** = utilisateur de destination de `sudo`. Par défaut
>   `root`. Pour `sudo -u app` : `runas: app`.
> - **Fichier généré** : `/etc/sudoers.d/<name>` (pas `/etc/sudoers`).
>   `validate: 'visudo -cf %s'` est appliqué automatiquement par le module.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-utilisateurs/sudoers/challenge/solution.yml
ansible db1.lab -b -m ansible.builtin.shell -a "ls -la /etc/sudoers.d/lab-rhce-*"
ansible db1.lab -b -m ansible.builtin.shell -a "visudo -cf /etc/sudoers"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-utilisateurs/sudoers/challenge/tests/
```

Le test vérifie en particulier les **permissions strictes 0440** sur les
fichiers (sinon `sudo` les ignore par sécurité).

## 🧹 Reset

```bash
make -C labs/modules-utilisateurs/sudoers clean
```

## 💡 Pour aller plus loin

- **`validation: required`** : Ansible valide la syntaxe via `visudo` avant
  d'écrire le fichier. Si le fichier généré est invalide, l'écriture
  échoue (filet de sécurité — le fichier d'origine reste intact).
- **`Defaults`** : pour poser des `Defaults env_keep+="HTTP_PROXY"` ou
  `Defaults requiretty`, utilisez `setenv:` ou éditez directement
  `/etc/sudoers.d/` via `template:`.
- **Lint** :

   ```bash
   ansible-lint labs/modules-utilisateurs/sudoers/challenge/solution.yml
   ```
