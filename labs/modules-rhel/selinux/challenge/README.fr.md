# 🎯 Challenge — SELinux pour servir une app web custom

## ✅ Objectif

Sur **db1.lab**, préparer **SELinux** pour que le serveur web (nginx) puisse :

1. Faire des **connexions réseau sortantes** (booléen
   `httpd_can_network_connect`).
2. **Servir** des fichiers depuis un dossier **custom** (`/var/www/myapp/`)
   en posant le contexte SELinux `httpd_sys_content_t`.

C'est un cas RHCE classique : déployer une app dans un dossier qui n'est pas
la racine web par défaut (`/usr/share/nginx/html/` pour nginx sur RHEL).

> 💡 **Pourquoi des booléens et un type en `httpd_` alors qu'on déploie
> nginx ?** Parce que sur RHEL, nginx tourne dans le **domaine SELinux
> `httpd_t`**, le domaine générique des serveurs web de la politique targeted.
> Vérifiez-le : `ps -eZ | grep nginx` affiche `system_u:system_r:httpd_t:s0`.
> `httpd_can_network_connect` et `httpd_sys_content_t` s'appliquent donc à
> nginx exactement comme à Apache. Le paquet `httpd` n'est jamais requis pour
> ce lab.

## 🧩 6 étapes

1. **Installer prérequis** : `python3-libselinux` et
   `policycoreutils-python-utils` (les modules Ansible SELinux dépendent de ces
   binaires côté managed node).
2. **SELinux enforcing** : `state: enforcing`, `policy: targeted`.
3. **Activer le booléen** `httpd_can_network_connect` (persistant).
4. **Créer le dossier** `/var/www/myapp/` (mode 0755).
5. **Définir le contexte** `httpd_sys_content_t` sur `/var/www/myapp(/.*)?`
   via `community.general.sefcontext` (regex de chemin).
6. **Appliquer le contexte** avec `restorecon -R /var/www/myapp` (sans cette
   étape, le contexte est dans la **policy** mais pas sur les **fichiers**
   existants).

## 🧩 Modules à utiliser

| Module | Rôle |
| --- | --- |
| `ansible.posix.selinux` | Mode global (enforcing/permissive/disabled) |
| `ansible.posix.seboolean` | Activer/désactiver un booléen SELinux |
| `community.general.sefcontext` | Définir un contexte sur un chemin (regex) |
| `ansible.builtin.command: restorecon ...` | Appliquer le contexte |

## 🧩 Squelette

```yaml
---
- name: Challenge - SELinux pour app web custom
  hosts: db1.lab
  become: true

  tasks:
    - name: Installer prérequis SELinux
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: SELinux enforcing
      ansible.posix.selinux:
        policy: ???
        state: ???

    - name: Activer le booléen httpd_can_network_connect
      ansible.posix.seboolean:
        name: ???
        state: ???
        persistent: ???

    - name: Créer /var/www/myapp
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Définir le contexte httpd_sys_content_t
      community.general.sefcontext:
        target: ???        # regex : '/var/www/myapp(/.*)?'
        setype: ???
        state: present

    - name: Appliquer le contexte avec restorecon
      ansible.builtin.command: restorecon -R /var/www/myapp
      changed_when: false
```

> 💡 **Pièges** :
>
> - **`seboolean`** est dans **`ansible.posix`**. **`sefcontext`** est dans
>   **`community.general`**. Bien différencier les FQCN.
> - **`sefcontext`** modifie la **politique** mais n'applique pas
>   immédiatement. `restorecon` est nécessaire pour appliquer aux fichiers
>   existants.
> - **`persistent: true`** sur `seboolean` : survie au reboot. Sans,
>   le booléen retombe au défaut au prochain démarrage.
> - **`python3-libselinux`** doit être installé sur la cible. Sans, les
>   modules `seboolean`/`sefcontext` plantent avec une erreur peu claire.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-rhel/selinux/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "getenforce"
ansible db1.lab -m ansible.builtin.command -a "getsebool httpd_can_network_connect"
ansible db1.lab -m ansible.builtin.command -a "ls -dZ /var/www/myapp"
```

## 🧪 Validation automatisée

> ⏱️ **Un test redémarre db1** (environ 90 s). Il est marqué `slow`, et il est
> là volontairement : la persistance après redémarrage est le piège qui fait
> échouer les candidats RHCSA et RHCE, et lire le fichier de configuration
> n'en prouve rien. Le temps de vos essais, vous pouvez l'écarter :
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/selinux/challenge/tests/
> ```
>
> Lancez la suite complète au moins une fois avant de considérer le
> challenge terminé.

```bash
pytest -v labs/modules-rhel/selinux/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-selinux
```

## 💡 Pour aller plus loin

- **`getsebool -a`** : liste tous les booléens SELinux et leur état.
- **`semanage fcontext -l | grep myapp`** : voir les contextes définis dans
  la policy (ce que `sefcontext` modifie).
- **AVC denials** : `ausearch -m AVC -ts recent` pour voir les refus SELinux
  récents — précieux pour comprendre pourquoi un service ne démarre pas.
- **Lint** :

   ```bash
   ansible-lint labs/modules-rhel/selinux/challenge/solution.yml
   ```
