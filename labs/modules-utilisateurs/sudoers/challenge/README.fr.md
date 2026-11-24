# Refaire les droits sudo après l'ère du « tout le monde est root »

## La situation

L'audit de **db1.lab** a trouvé ce qui arrive quand sudo pousse tout seul :
quelques personnes disposent du root complet, sans mot de passe, et personne ne
se souvient de l'avoir accordé. Il reste trois besoins légitimes, et trois
seulement. Alice administre la machine, mais doit ressaisir son mot de passe
pour qu'un terminal volé ne soit pas un shell root gratuit. L'équipe ops
automatise et ne peut pas s'arrêter sur une invite. Et Alice doit lancer le
script de déploiement **en tant que compte de service**, sans devenir root. Une
faute de frappe dans un fichier sudo verrouille toute l'équipe dehors.

Votre mission :

1. Depuis **control-node.lab**, poser les prérequis sur **db1.lab** : les
   comptes, le groupe ops et son appartenance.
2. Accorder à Alice le **sudo complet avec mot de passe exigé**, et au groupe
   ops le **sudo complet sans mot de passe** : attention au défaut du module, il
   ne penche pas du côté que l'on espère.
3. Autoriser Alice à lancer **le seul script de déploiement**, et **en tant que
   compte deploy**, pas en root.
4. Faire atterrir chaque règle dans **son propre fichier sous
   `/etc/sudoers.d/`**, validé syntaxiquement avant toute écriture sur le disque.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-sudoers/

## 🎯 Challenge — Règles sudo granulaires

### ✅ Objectif

Sur **db1.lab**, créer **3 règles sudo** dans `/etc/sudoers.d/` via le module
`community.general.sudoers`.

### 🧩 Règles à provisionner

| Fichier | User/Groupe | Commandes | Mot de passe ? | RunAs |
| --- | --- | --- | --- | --- |
| `lab-rhce-alice` | user `alice` | `ALL` | **oui** (avec password) | (défaut) |
| `lab-rhce-ops-team` | groupe `ops-team` | `ALL` | non (`NOPASSWD`) | (défaut) |
| `lab-rhce-alice-as-deploy` | user `alice` | `/opt/myapp/bin/deploy.sh` | non | `deploy` |

### 🧩 Pré-requis (étape `users`)

Avant les règles sudo, créez :

- Users : `alice`, `bob`, `deploy`.
- Groupe : `ops-team`.
- `bob` membre du groupe `ops-team` (`groups: ops-team, append: true`).

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-utilisateurs-sudoers
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧩 Squelette

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

### 🚀 Lancement

```bash
ansible-playbook labs/modules-utilisateurs/sudoers/challenge/solution.yml
ansible db1.lab -b -m ansible.builtin.shell -a "ls -la /etc/sudoers.d/lab-rhce-*"
ansible db1.lab -b -m ansible.builtin.shell -a "visudo -cf /etc/sudoers"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-utilisateurs/sudoers/challenge/tests/
```

Le test vérifie en particulier les **permissions strictes 0440** sur les
fichiers (sinon `sudo` les ignore par sécurité).

### 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-sudoers
```

### 💡 Pour aller plus loin

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
