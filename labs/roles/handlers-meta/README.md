# Lab 60 — Rôles : `handlers/` et `meta/`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Rôles Ansible : handlers et meta**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/handlers-meta/)

Au [lab 58](../58-roles-creer-premier-role/), vous avez créé votre premier
rôle (squelette `tasks/main.yml`). Au [lab 59](../59-roles-variables-defaults-vars/),
vous avez vu `defaults/` et `vars/`. Ce lab couvre **les deux derniers
sous-dossiers fondamentaux** d'un rôle :

| Dossier | Rôle | Visibilité |
| --- | --- | --- |
| `handlers/main.yml` | Tâches **réactives** déclenchées par `notify:` | Tasks du rôle + tâches externes (si rôle inclus) |
| `meta/main.yml` | **Carte d'identité** du rôle (Galaxy info, plateformes, dépendances) | Lu par `ansible-galaxy`, `ansible-lint`, et la résolution de dépendances |

> 💡 **Différence clé** avec les handlers d'un play : ceux du rôle vivent
> dans le **scope du rôle**. Un handler `Restart nginx` dans `roles/webserver/handlers/`
> est appelable par `notify: Restart nginx` depuis n'importe où — y compris
> depuis un autre rôle ou depuis le play parent.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un fichier `handlers/main.yml` avec **plusieurs handlers** (Restart, Reload, Notification custom).
2. Distinguer **`state: restarted`** vs **`state: reloaded`** dans un handler — quand utiliser l'un ou l'autre.
3. Notifier un handler avec **`notify:`** sur une tâche d'un rôle.
4. Écrire un **handler non-service** (ex. log, webhook, fichier) — un handler n'est pas qu'un `systemd_service`.
5. Compléter `meta/main.yml` avec **`galaxy_info`**, **`platforms`**, **`galaxy_tags`**, **`min_ansible_version`**, **`license`**.
6. Comprendre **`dependencies: []`** et **`allow_duplicates: false`**.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.shell \
    -a "rm -f /var/log/webserver-deploy.log /var/log/deploy-notification.log"
```

## ⚙️ Arborescence du lab

```text
labs/roles/handlers-meta/
├── README.md                                ← ce fichier
├── Makefile                                 ← cible `clean`
├── roles/
│   └── webserver/                           ← rôle de référence livré
│       ├── tasks/main.yml                   ← notifie 3 handlers différents
│       ├── handlers/main.yml                ← À ÉTUDIER (3 handlers)
│       ├── defaults/main.yml                ← (rappel lab 59)
│       ├── meta/main.yml                    ← À ÉTUDIER (galaxy_info)
│       └── templates/nginx.conf.j2
└── challenge/
    ├── README.md                            ← consigne du challenge
    └── tests/
        └── test_handlers.py                 ← pytest+testinfra
```

> ⚠️ **Convention** : le rôle `webserver` est livré pré-écrit pour ce lab.
> L'objectif n'est **pas** de réécrire le rôle, mais de **comprendre** et
> **utiliser** ses handlers + de **lire** son `meta/`.

## 📚 Exercice 1 — Lire `handlers/main.yml`

Ouvrez `roles/webserver/handlers/main.yml` :

```yaml
- name: Restart nginx
  ansible.builtin.systemd_service:
    name: "{{ webserver_package }}"
    state: restarted

- name: Reload nginx
  ansible.builtin.systemd_service:
    name: "{{ webserver_package }}"
    state: reloaded

- name: Notify deployment
  ansible.builtin.copy:
    dest: /var/log/deploy-notification.log
    content: |
      Deployment completed: {{ ansible_date_time.iso8601 }}
      Host: {{ inventory_hostname }}
      Webserver port: {{ webserver_listen_port }}
    mode: "0644"
```

🔍 **Observation** — 3 handlers, 3 cas d'usage :

| Handler | Quand le déclencher ? | Effet |
| --- | --- | --- |
| `Restart nginx` | Après suppression d'un fichier de conf (`conf.d/default.conf`) — nécessite un redémarrage complet | Downtime ~1s |
| `Reload nginx` | Après modification de `nginx.conf` — nginx sait recharger en live (SIGHUP) | Pas de downtime |
| `Notify deployment` | À la fin d'un déploiement réussi — purement informationnel | Aucun impact service |

**Règle générale** :

- **Reload** > Restart quand le service le supporte (HUP signal). Pas de downtime.
- **Restart** quand un changement majeur (binaire upgradé, conf incompatible avec live reload).
- Un handler peut être **n'importe quelle tâche** — pas que `systemd_service`. Ici on log dans un fichier.

## 📚 Exercice 2 — Lire `tasks/main.yml` (qui notifie quoi)

Ouvrez `roles/webserver/tasks/main.yml`. Repérez les `notify:` :

| Tâche | `notify:` | Pourquoi |
| --- | --- | --- |
| Supprimer la conf par défaut conflictuelle | `Restart nginx` | Suppression de fichier → reload ne suffit pas |
| Déployer nginx.conf depuis le template | `Reload nginx` | Modif de conf → SIGHUP suffit |
| Déployer la page d'accueil | (aucun) | Page HTML — nginx la sert sans reload |
| Tracer le déploiement | `Notify deployment` | Log final, après tout le reste |

🔍 **Observation** : un handler n'est notifié que si la tâche est `changed`.
La tâche « Tracer le déploiement » utilise `copy:` avec un timestamp dans
le contenu — donc **toujours `changed`** → le handler `Notify deployment`
tourne à chaque run. C'est voulu (notification de déploiement à chaque
exécution).

## 📚 Exercice 3 — Lire `meta/main.yml`

Ouvrez `roles/webserver/meta/main.yml` :

```yaml
galaxy_info:
  author: Stéphane Robert
  namespace: stephrobert
  role_name: webserver
  description: |
    Installer et configurer nginx ...
  license: MIT
  min_ansible_version: "2.16"

  platforms:
    - name: EL
      versions: ["9", "10"]
    - name: AlmaLinux
      versions: ["9", "10"]

  galaxy_tags: [nginx, webserver, http, rhce]

dependencies: []
allow_duplicates: false
```

🔍 **Observation** — chaque champ a son rôle :

| Champ | Rôle | Conséquence si absent |
| --- | --- | --- |
| `author`, `namespace`, `role_name` | Identité Galaxy | Impossible de publier sur Galaxy |
| `description` | Affiché sur la page Galaxy | Page peu attractive |
| `license` | Licence légale (MIT, GPLv3, …) | Galaxy refuse la publication |
| `min_ansible_version` | Version Ansible minimale supportée | Risque de bug silencieux sur vieille Ansible |
| `platforms` | OS supportés par le rôle | Galaxy filtre par OS |
| `galaxy_tags` | Tags pour la recherche | Rôle invisible dans les recherches |
| `dependencies: []` | Liste de rôles dépendants | (pas de dépendances ici, lab 72 le couvre) |
| `allow_duplicates: false` | Refuse l'inclusion multiple du rôle | Bonne pratique sauf cas particulier |

## 📚 Exercice 4 — Lancer le rôle et observer les handlers

Créez un `playbook.yml` à la racine du lab qui utilise le rôle :

```yaml
---
- name: Démo handlers du rôle webserver
  hosts: db1.lab
  become: true
  roles:
    - role: webserver
```

Lancez-le :

```bash
ansible-playbook labs/roles/handlers-meta/playbook.yml
```

🔍 **Observation** — sortie console (extrait) :

```text
TASK [webserver : Supprimer la conf par défaut ...] *** changed (1er run)
TASK [webserver : Déployer nginx.conf ...]            *** changed (1er run)
TASK [webserver : Tracer le déploiement]              *** changed (toujours)

RUNNING HANDLER [webserver : Restart nginx]           *** changed
RUNNING HANDLER [webserver : Reload nginx]            *** changed
RUNNING HANDLER [webserver : Notify deployment]       *** changed
```

**3 handlers déclenchés** au 1er run.

```bash
# Vérifier les fichiers de log
ssh ansible@db1.lab 'sudo cat /var/log/webserver-deploy.log'
ssh ansible@db1.lab 'sudo cat /var/log/deploy-notification.log'
```

Au **2ème run** : seuls les handlers liés à des **vraies modifs** se relancent
(donc `Notify deployment` à cause du timestamp, mais pas `Restart` ni `Reload`
car la conf est inchangée).

## 🔍 Observations à noter

- **Handlers d'un rôle** vivent dans `handlers/main.yml`. Ils sont scoped au
  rôle mais notifiables depuis l'extérieur (avec préfixe `<role_name> :`).
- **`reloaded` > `restarted`** quand le service le supporte (nginx, apache,
  postgresql, sshd…). Pas de downtime.
- **Un handler peut être n'importe quelle tâche** — copy, debug, uri,
  shell. Pas réservé aux `systemd_service`.
- **`meta/main.yml`** est lu par `ansible-galaxy`, `ansible-lint --profile
  production`, et le mécanisme de dépendances. **Toujours le remplir**
  pour un rôle qu'on partage.
- **`allow_duplicates: false`** (défaut) : empêche d'inclure le même rôle
  plusieurs fois dans un play. À mettre à `true` uniquement si vous voulez
  appliquer le même rôle avec des params différents (ex : déployer 3
  vhosts nginx).

## 🤔 Questions de réflexion

1. Vous avez 3 tâches qui modifient `nginx.conf`. Combien de fois le handler
   `Reload nginx` tourne-t-il ? Pourquoi ?

2. Le handler `Notify deployment` log à chaque run. Est-ce un anti-pattern
   d'idempotence ? Comment le corriger pour qu'il ne notifie que si quelque
   chose a vraiment changé ?

3. Vous voulez que votre rôle dépende de `geerlingguy.firewall` (pour ouvrir
   les ports). Dans quel champ de `meta/main.yml` le déclarez-vous ? (Indice :
   le lab 72 le couvre.)

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`listen:`** sur un handler : permet à plusieurs handlers d'écouter un
  même topic abstrait (cf. lab 06).
- **`meta: flush_handlers`** : force l'exécution immédiate des handlers en
  attente (cf. lab 06).
- **`force_handlers: true`** au niveau play : exécute les handlers en attente
  même si une tâche échoue ensuite. Précieux pour ne pas laisser un
  service en config moitié-modifiée.
- **`dependencies:`** dans `meta/main.yml` : listez d'autres rôles à exécuter
  **avant** le vôtre. Couvert au lab 72.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `playbook.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint du rôle complet
ansible-lint labs/roles/handlers-meta/roles/webserver/

# Lint de votre solution challenge
ansible-lint labs/roles/handlers-meta/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/roles/handlers-meta/
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques.
