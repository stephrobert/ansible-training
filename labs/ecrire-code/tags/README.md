# Lab 07 — Tags (cibler ou ignorer un sous-ensemble de tâches)

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

🔗 [**Tags Ansible : cibler ou ignorer un sous-ensemble de tâches**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/tags/)

Quand un playbook grossit (50, 100 tâches), vous ne voulez pas **tout** rejouer à chaque modif. Les **tags** sont des étiquettes qu'on pose sur les tâches pour pouvoir les **cibler** au lancement :

```bash
ansible-playbook playbook.yml --tags install        # ne joue que les tâches taguées "install"
ansible-playbook playbook.yml --skip-tags database  # joue tout sauf "database"
```

Les tags peuvent être posés sur une **tâche**, un **block**, un **play entier**, ou un **rôle**. Ils s'**héritent** du conteneur vers les enfants.

Tags spéciaux à connaître :

| Tag | Comportement |
| --- | --- |
| **`always`** | La tâche s'exécute **toujours**, même si vous filtrez `--tags autre`. Exception : `--skip-tags always` la coupe. |
| **`never`** | La tâche **ne s'exécute jamais**, sauf si on lance explicitement `--tags <son tag>`. |
| **`tagged`** | Filtre méta : exécute uniquement les tâches qui ont **au moins un tag**. |
| **`untagged`** | Filtre méta : exécute uniquement les tâches **sans aucun tag**. |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Poser un **tag** sur une tâche et plusieurs tâches.
2. Cibler un sous-ensemble avec **`--tags`** et exclure avec **`--skip-tags`**.
3. Inspecter le plan d'exécution sans rien lancer (`--list-tags`, `--list-tasks`).
4. Utiliser le tag spécial **`always`** pour des tâches incontournables (logs, marqueurs).
5. Utiliser le tag spécial **`never`** pour des tâches dangereuses (reset, drop).
6. Comprendre l'**héritage** des tags depuis un `block:` ou un play.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ansible.builtin.ping
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
```

Réponse attendue : `pong`. Le second `ansible` nettoie les marqueurs des runs précédents.

## ⚙️ Arborescence cible

```text
labs/ecrire-code/tags/
├── README.md           ← ce fichier
├── playbook.yml        ← À CRÉER — votre play avec tags
└── challenge/
    ├── README.md       ← challenge final (déjà présent)
    └── tests/
        └── test_*.py   ← (déjà présent — pytest+testinfra)
```

## 📚 Exercice 1 — Squelette du playbook

Créez `labs/ecrire-code/tags/playbook.yml` avec 3 tâches qui posent chacune un fichier marqueur :

```yaml
---
- name: Démo tags Ansible
  hosts: web1.lab
  become: true

  tasks:
    # Tâche 1 — taguée install
    # Tâche 2 — taguée configuration
    # Tâche 3 — taguée service
```

🔍 **Observation** : un tag est juste un mot-clé `tags:` ajouté à une tâche. Aucune contrainte sur le nom — choisissez ce qui décrit la phase logique (`install`, `configuration`, `database`, `cleanup`…).

## 📚 Exercice 2 — Trois tâches taguées

Pour chaque tâche, utilisez `ansible.builtin.copy` avec `content:`. Voici la première en exemple :

```yaml
- name: Marqueur stage install
  ansible.builtin.copy:
    dest: /tmp/tag-install.txt
    content: "install posé à {{ ansible_date_time.iso8601 }}\n"
    mode: "0644"
  tags: install
```

Faites de même pour les tags `configuration` (dest = `/tmp/tag-configuration.txt`) et `service` (dest = `/tmp/tag-service.txt`).

🔍 **Observation à anticiper** : `tags:` accepte une **valeur unique** (`tags: install`) ou une **liste** (`tags: [install, fast]`). Les deux formes sont valides.

## 📚 Exercice 3 — Lancer **sans filtre** (cas par défaut)

Sans option `--tags`, **toutes** les tâches tournent :

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml
```

🔍 **Observation** : `PLAY RECAP` affiche `ok=4 changed=3` (les 3 tâches + le `gather_facts`). Les 3 marqueurs sont posés :

```bash
ssh ansible@web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt /tmp/tag-install.txt /tmp/tag-service.txt
```

## 📚 Exercice 4 — Cibler un seul tag avec `--tags`

Nettoyez les marqueurs et relancez en **ciblant** uniquement `configuration` :

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration
```

🔍 **Observation** : `PLAY RECAP` affiche `ok=1 changed=1 skipped=2`. Les tâches `install` et `service` sont **skippées** (Ansible voit qu'elles n'ont pas le tag demandé).

```bash
ssh ansible@web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt    ← seul ce fichier existe
```

## 📚 Exercice 5 — Exclure un tag avec `--skip-tags`

Inverse du précédent : tout, **sauf** `service`.

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --skip-tags service
```

🔍 **Observation** : `install` et `configuration` tournent ; `service` est skippé. C'est utile en pratique pour « tout sauf la partie qui prend 10 min ».

## 📚 Exercice 6 — Inspecter sans exécuter (`--list-tags`, `--list-tasks`)

Avant de lancer un long playbook avec un filtre, vérifiez que vous ciblez bien ce que vous croyez :

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --list-tags
```

🔍 **Observation** : sortie attendue :

```text
play #1 (web1.lab): Démo tags Ansible    TAGS: []
    TASK TAGS: [configuration, install, service]
```

Pour voir **quelles tâches** seraient exécutées avec un filtre donné :

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --list-tasks --tags configuration
```

C'est l'équivalent d'un **dry-run de la sélection** — sans rien lancer ni se connecter aux managed nodes.

## 📚 Exercice 7 — Tag spécial `always` (la tâche incontournable)

Ajoutez une 4e tâche **avant** les autres, taguée `always`. Elle servira de marqueur universel — peu importe le filtre passé, elle tourne toujours.

```yaml
- name: Marqueur run (always)
  ansible.builtin.copy:
    dest: /tmp/tag-run.txt
    content: "run lancé à {{ ansible_date_time.iso8601 }}\n"
    mode: "0644"
  tags: always
```

Testez :

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration
ssh ansible@web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt /tmp/tag-run.txt    ← run.txt existe alors qu'on a filtré configuration !
```

🔍 **Observation** : `always` ignore le filtre `--tags`. **Cas d'usage typique** : pose d'un timestamp de début, log de qui a lancé le playbook, vérification de prérequis. À utiliser avec parcimonie — un play plein d'`always` est un play sans tags utiles.

## 📚 Exercice 8 — Tag spécial `never` (la tâche dangereuse)

Ajoutez une 5e tâche taguée `[never, reset]` qui supprime tous les marqueurs :

```yaml
- name: Marqueur reset destructif
  ansible.builtin.shell: rm -f /tmp/tag-*.txt
  tags: [never, reset]
```

Testez **deux** scénarios :

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml                    # sans filtre
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration   # filtre configuration
```

🔍 **Observation** : dans **les deux cas**, la tâche `reset` est **skippée**. `never` est plus fort que tout — sauf si on demande **explicitement** son tag :

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags reset
```

C'est seulement là qu'elle s'exécute. **Cas d'usage typique** : opérations destructives (drop database, suppression de fichiers, reset de config) qu'on ne veut **jamais** voir tourner par accident.

## 📚 Exercice 9 — Héritage : un tag sur un `block:`

Au lieu de répéter `tags: install` sur 5 tâches, posez-le **une fois** sur un `block:` qui les regroupe :

```yaml
tasks:
  - name: Phase d'installation
    block:
      - name: Tâche 1 install
        ansible.builtin.copy:
          dest: /tmp/tag-install-1.txt
          content: "install 1\n"
          mode: "0644"

      - name: Tâche 2 install
        ansible.builtin.copy:
          dest: /tmp/tag-install-2.txt
          content: "install 2\n"
          mode: "0644"
    tags: install      # hérité par les 2 tâches du block
```

🔍 **Observation** : `--tags install` joue les deux tâches, alors qu'aucune n'a de `tags:` propre. C'est la règle d'**héritage** : un tag sur un conteneur (block, play, rôle) est ajouté à toutes les tâches enfants.

## 🔍 Observations à noter

- Un tag est **purement organisationnel** — c'est juste une étiquette. Aucun comportement par défaut associé (sauf les 4 spéciaux).
- **`--tags A,B`** exécute les tâches taguées A **OU** B (union). **`--skip-tags A,B`** ignore les tâches taguées A ou B.
- L'**héritage** propage de play → block → tâche. Une tâche cumule ses tags propres + ceux hérités.
- **`always`** = toujours sauf `--skip-tags always`. **`never`** = jamais sauf `--tags <son tag>`. Pas de symétrie parfaite — à mémoriser.
- **`--list-tags` et `--list-tasks`** sont vos amis avant un long playbook. Pas besoin de se connecter aux managed nodes pour les utiliser.
- **Convention de nommage** : utiliser des verbes/phases courts (`install`, `configure`, `deploy`, `cleanup`). Évitez les tags génériques (`tag1`, `important`) qui n'aident personne.

## 🤔 Questions de réflexion

1. Vous avez 3 tags `install`, `configure`, `start`. Vous voulez relancer **uniquement** la partie configuration **et** redémarrage du service, **sans** réinstaller. Quelle commande ?

2. Vous écrivez un playbook qui contient une tâche `Drop la base de production`. Quel tag mettre dessus pour qu'elle ne tourne **jamais** par accident, même si un collègue lance `--tags database` ?

3. Vous voulez lancer **uniquement** les tâches **non taguées** d'un long playbook (audit / nettoyage). Quel tag spécial filtrer ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) consolide les exos 7 et 8 sur `db1.lab` : une tâche `always` (marqueur), une `configuration` standard, et une tâche `[never, reset]` destructive. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v labs/ecrire-code/tags/challenge/tests/
```

## 💡 Pour aller plus loin

- **Tags par environnement** : `tags: [prod, deploy]` sur certaines tâches, `tags: [staging, deploy]` sur d'autres. Lancez `--tags "prod,deploy"` pour cibler la prod uniquement.
- **Tags + `--check`** : `ansible-playbook playbook.yml --tags configure --check --diff`. C'est le **dry-run filtré** — rapide, sûr, ciblé. Pattern idéal en pré-prod.
- **Tags hérités d'un rôle** : si vous incluez un rôle avec `roles: [{ role: webserver, tags: [web] }]`, **toutes** les tâches du rôle reçoivent le tag `web`. Une commande, un rôle entier ciblé.
- **`meta: end_play`** vs **`tags: never`** : `end_play` arrête le play **conditionnellement** (avec `when:`), `never` exclut **statiquement**. Choisir selon que la décision est runtime ou structurelle.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/tags/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/tags/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/tags/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
