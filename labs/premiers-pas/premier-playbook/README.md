# Lab 04 — Premier playbook (installer nginx sur les webservers)

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

🔗 [**Premier playbook Ansible : installer nginx, ouvrir le port 80, démarrer le service**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premier-playbook/)

C'est votre **premier vrai playbook** — celui où vous écrivez vous-même le YAML. La page du blog présente l'**anatomie d'un playbook** :

```yaml
---
- name: <nom du play>          # un texte libre, affiché dans la console
  hosts: <pattern>             # quels managed nodes cibler (ex: webservers, all, web1.lab)
  become: true                 # sudo (élévation root)
  gather_facts: true           # collecter les facts au démarrage

  tasks:                       # liste de tâches, exécutées dans l'ordre
    - name: <description>      # toujours nommer ses tâches !
      ansible.builtin.<module>:
        param1: valeur1
        param2: valeur2
```

Chaque **tâche** appelle un **module**. Un module est un mini-programme qui fait **une seule chose** (installer un paquet, copier un fichier, démarrer un service…). On en utilisera 5 dans ce lab : `dnf`, `systemd`, `firewalld`, `uri`, `debug`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un playbook YAML qui **enchaîne 5 tâches**.
2. L'exécuter avec `ansible-playbook` sur le groupe `webservers`.
3. Lire le **`PLAY RECAP`** et identifier `ok` / `changed` / `failed`.
4. Vérifier l'**idempotence** au second passage (`changed=0`).
5. Capturer la sortie d'une tâche dans une variable avec **`register:`**.
6. Tester depuis l'extérieur que le service web répond.

## 🔧 Préparation

Vérifiez que les 2 webservers sont joignables :

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ansible.builtin.ping
```

Réponse attendue : 2 `pong` (un pour `web1.lab`, un pour `web2.lab`).

> 💡 Toutes les commandes `ansible-playbook` se lancent **depuis la racine du repo** — c'est ce qui permet à l'inventaire de résoudre `{{ inventory_dir }}/../ssh/id_ed25519`.

## ⚙️ Arborescence cible (à construire vous-même)

```text
labs/premiers-pas/premier-playbook/
├── README.md          ← ce fichier (déjà présent)
├── playbook.yml       ← À CRÉER — votre premier playbook
└── challenge/
    ├── README.md      ← challenge final (déjà présent)
    └── tests/
        └── test_*.py  ← pytest+testinfra (déjà présent)
```

## 📚 Exercice 1 — Squelette du playbook

Créez `labs/premiers-pas/premier-playbook/playbook.yml` avec le squelette ci-dessous. Les 5 tâches viendront ensuite, dans l'ordre.

```yaml
---
- name: Déployer nginx sur les webservers
  hosts: webservers
  become: true
  gather_facts: true

  tasks:
    # Vous allez écrire les 5 tâches ci-dessous, dans cet ordre.
```

🔍 **Observation** — chaque ligne du squelette compte :

- **`hosts: webservers`** → cible le groupe défini dans `inventory/hosts.yml` (donc `web1.lab` + `web2.lab`).
- **`become: true`** → tout le play s'exécute en root via `sudo`. Sans ça, `dnf install` échoue sur « Permission denied ».
- **`gather_facts: true`** → Ansible collecte ~200 variables sur chaque hôte au démarrage (OS, IP, mémoire, etc.). C'est le défaut, mais on le rend explicite ici pour bien marquer cette étape.

## 📚 Exercice 2 — Tâche 1 : installer nginx

Dans `tasks:`, ajoutez la première tâche. Le module `ansible.builtin.dnf` installe (ou supprime) un paquet RPM.

Indices :

- Module : `ansible.builtin.dnf` (FQCN obligatoire RHCE).
- `name: nginx`
- `state: present` (présent — installer si absent, ne rien faire sinon).

Pour vous aider, lancez la doc :

```bash
ansible-doc ansible.builtin.dnf | less
```

🔍 **Observation à anticiper** : au premier run, cette tâche affichera `changed` (paquet installé). Au second run, `ok` (déjà présent).

## 📚 Exercice 3 — Tâche 2 : démarrer et activer nginx

Le paquet est installé mais **le service n'est pas démarré** (paquet `nginx` sur RHEL/AlmaLinux ne s'auto-démarre pas). Ajoutez une tâche `ansible.builtin.systemd` qui :

- `name: nginx`
- `state: started` (démarrer maintenant)
- `enabled: true` (activer au boot)

🔍 **Observation à anticiper** : `state: started` ≠ `state: restarted`. `started` est **idempotent** (ne fait rien si déjà actif), `restarted` redémarre **à chaque run**. Vous utiliserez `restarted` plus tard via les **handlers** (lab 06).

## 📚 Exercice 4 — Tâche 3 : ouvrir le port 80 dans firewalld

AlmaLinux 10 a `firewalld` activé par défaut, donc le port 80 est **fermé** même si nginx écoute dessus. Ajoutez une tâche `ansible.posix.firewalld` qui ouvre le service `http` :

- `service: http` (firewalld connaît `http` comme alias de port 80/tcp)
- `permanent: true` (règle persistante au reboot)
- `immediate: true` (règle appliquée tout de suite, sans `firewall-cmd --reload`)
- `state: enabled`

> ⚠️ **Piège classique** : si vous oubliez `immediate: true`, la règle est écrite mais **pas appliquée**. Le test depuis votre poste retournera `Connection refused` jusqu'au prochain reload du firewall.

🔍 **Observation à anticiper** : module `ansible.posix.firewalld` (pas `ansible.builtin`) — il vient de la collection `ansible.posix` installée au lab 02.

## 📚 Exercice 5 — Tâche 4 : tester avec `uri` et capturer la réponse

Avant de déclarer victoire, on **teste**. Le module `ansible.builtin.uri` fait une requête HTTP **depuis le managed node** :

- `url: http://localhost`
- `status_code: 200` (échoue si le code retourné n'est pas 200)
- **`register: nginx_response`** (capture toute la réponse dans une variable)

🔍 **Observation à anticiper** : `register:` est le pont entre une tâche et celle qui suit. La variable `nginx_response` contient un dict avec `status`, `url`, `content`, `elapsed`, etc. Vous l'utilisez dans la tâche suivante.

## 📚 Exercice 6 — Tâche 5 : afficher le résultat avec `debug`

Pour confirmer que tout est OK, affichez le code HTTP capturé. Module `ansible.builtin.debug` :

- `msg: "nginx répond avec le code {{ nginx_response.status }} sur {{ inventory_hostname }}"`

Indices :

- `{{ nginx_response.status }}` → l'attribut `status` du dict capturé à l'exo 5.
- `{{ inventory_hostname }}` → variable magique = nom de l'hôte courant dans la boucle Ansible.
- Les `{{ }}` sont la syntaxe Jinja2 d'interpolation.

## 📚 Exercice 7 — Exécuter le playbook

Depuis la racine du repo :

```bash
ansible-playbook labs/premiers-pas/premier-playbook/playbook.yml
```

🔍 **Observation** — le `PLAY RECAP` au **premier passage** ressemble à :

```text
PLAY RECAP *********************************************************************
web1.lab    : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2.lab    : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Décryptage des colonnes :

- **`ok=6`** : 6 tâches ont rendu un statut OK (vos 5 tâches + le `gather_facts` initial).
- **`changed=3`** : 3 tâches ont **modifié** l'état du système (install dnf, démarrage systemd, ouverture firewalld). Les tâches `uri` et `debug` ne modifient rien — elles sont `ok` mais pas `changed`.
- **`failed=0`** : aucune erreur.

## 📚 Exercice 8 — Vérifier l'idempotence

Relancez **immédiatement** la même commande :

```bash
ansible-playbook labs/premiers-pas/premier-playbook/playbook.yml
```

🔍 **Observation** : le `PLAY RECAP` doit afficher **`changed=0`** :

```text
web1.lab    : ok=6    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

C'est la **preuve mécanique d'idempotence** (vu au lab 01). Vos 3 tâches « modifiantes » ont vu que l'état désiré était déjà appliqué et n'ont **rien fait**. C'est ce qui rend Ansible sûr à relancer 100 fois.

## 📚 Exercice 9 — Tester depuis votre poste

Depuis votre poste de travail (le control node) :

```bash
curl -I http://10.10.20.21
curl -I http://10.10.20.22
```

🔍 **Observation** : vous devez voir `HTTP/1.1 200 OK` et un header `Server: nginx/...`. Si vous obtenez `Connection refused`, vérifiez l'exo 4 (le `immediate: true` du firewalld).

## 🔍 Observations à noter

- Un **playbook minimal** = `name` + `hosts` + `tasks`. `become` et `gather_facts` sont des options (avec des défauts).
- **FQCN** (`ansible.builtin.dnf`) au lieu du nom court (`dnf`) : obligatoire RHCE, recommandé partout. Garantit qu'on appelle bien le module attendu.
- Le **`PLAY RECAP`** est votre **tableau de bord** : `ok`, `changed`, `failed`, `unreachable`. Une tâche peut être `ok` sans être `changed` (lecture seule, vérification).
- `state: started` (idempotent) ≠ `state: restarted` (action systématique). Pareil pour `present` / `latest` sur `dnf`.
- **`register:`** + **`{{ var.attribut }}`** = pattern de base pour chaîner deux tâches.
- `ansible.builtin.*` est livré avec `ansible-core`. Les autres collections (ex : `ansible.posix.firewalld`) doivent être installées via `ansible-galaxy`.

## 🤔 Questions de réflexion

1. Vous changez `state: present` en `state: latest` sur la tâche `dnf`. Que se passe-t-il au second run ? Est-ce toujours idempotent ? Pourquoi ?

2. Vous oubliez `become: true` au niveau du play. Quelle tâche échoue en premier, et avec quel message ? (Indice : `dnf install` requiert root.)

3. Vous voulez **n'exécuter le test `uri`** que si nginx vient d'être démarré (et pas à chaque run). Quel mot-clé Ansible permet ça ? (Indice : on le verra au lab 20 — `when:`.)

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) vous demande de **réécrire la même logique** mais pour `httpd` (Apache) sur `db1.lab` au lieu de nginx sur les webservers. Les tests `pytest+testinfra` vérifieront automatiquement votre solution :

```bash
pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
```

C'est l'occasion de tester si vous avez vraiment compris le squelette — ou si vous avez juste copié.

## 💡 Pour aller plus loin

- **Mode `--check`** (lab 08) : `ansible-playbook playbook.yml --check` simule sans modifier. Très utile en pré-prod.
- **Tags** (lab 07) : taggez chaque tâche pour exécuter sélectivement (`--tags install` ne joue que la tâche d'installation).
- **Handlers** (lab 06) : remplacez la tâche `state: started` par un **handler** déclenché uniquement quand un fichier de config change. C'est le vrai pattern de production.
- **Variables** (lab 12) : externalisez `nginx`, `http`, `localhost` dans des variables réutilisables.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/premiers-pas/premier-playbook/lab.yml

# Lint de votre solution challenge
ansible-lint labs/premiers-pas/premier-playbook/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/premiers-pas/premier-playbook/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
