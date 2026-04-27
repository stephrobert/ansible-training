# Lab 08 — Check mode et diff (dry-run et visualisation)

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

🔗 [**Check mode et diff Ansible : dry-run et visualisation des changements**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/)

`--check` simule l'exécution sans appliquer les changements. `--diff` affiche le diff
unifié des fichiers modifiés. `check_mode: false` au niveau tâche force une exécution
réelle même en mode `--check`. Combinés, ces 3 outils sont **la base de toute
opération en production** — on valide d'abord, on applique ensuite.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Lancer** un playbook en `--check` et lire le `PLAY RECAP` correctement.
2. **Comparer** la sortie d'un run réel vs un run en `--check --diff`.
3. **Identifier** les modules qui supportent `--check` et ceux qui ne le supportent pas.
4. **Forcer** une tâche à s'exécuter en `--check` via `check_mode: false`.
5. **Diagnostiquer** un faux positif `changed=1` en `--check` qui n'aurait pas eu lieu en réel.

## 🔧 Préparation

Vérifier que `web1.lab` est joignable et que vous êtes au repo root :

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
# Doit retourner "pong"
```

S'assurer que `/etc/motd` existe (par défaut sur AlmaLinux, sinon créer un fichier vide) :

```bash
ansible web1.lab -m command -a "ls -la /etc/motd" -b
```

## 📚 Exercice 1 — Premier `--check` sur `copy:`

Créez le fichier `lab.yml` à la racine du lab :

```yaml
---
- name: Lab checkmode - exercice 1
  hosts: web1.lab
  become: true
  tasks:
    - name: Poser un MOTD personnalise
      ansible.builtin.copy:
        dest: /etc/motd
        content: "Bienvenue sur web1 — Ansible RHCE 2026\n"
        mode: "0644"
```

**Lancez en check mode** :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check
```

Vérifiez **immédiatement après** :

```bash
ansible web1.lab -m command -a "cat /etc/motd"
```

🔍 **Observation** : le `PLAY RECAP` annonce `changed=1`, mais `cat /etc/motd` ne montre
**pas** votre nouveau contenu. C'est normal — `--check` est un dry-run, **rien n'est
écrit** côté managed node. Le `changed=1` indique seulement *ce qui aurait changé*.

## 📚 Exercice 2 — Ajouter `--diff` pour voir le contenu exact

Relancez la même commande avec `--diff` :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation** : la sortie inclut maintenant un **diff unifié** :

```diff
--- before: /etc/motd
+++ after: /etc/motd
@@ -1 +1 @@
-Welcome to AlmaLinux 10.1
+Bienvenue sur web1 — Ansible RHCE 2026
```

Ce diff est **la matière première** d'une revue de changement avant déploiement.
En production, on **commit ce diff dans la PR** ou on l'envoie à l'équipe Ops avant
de lancer pour de vrai.

**Maintenant, exécution réelle** (sans `--check`) :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --diff
```

Vérifiez :

```bash
ansible web1.lab -m command -a "cat /etc/motd"
```

🔍 **Observation** : cette fois le contenu a bien changé.

## 📚 Exercice 3 — Re-exécuter en `--check` et comparer

Relancez **immédiatement** la même commande :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation** : `PLAY RECAP` annonce maintenant `changed=0`, et **aucun diff**
n'est affiché. C'est l'**idempotence** combinée à `--check` : Ansible compare le
checksum local au checksum du fichier sur web1, ils sont identiques, **pas de changement
projeté**.

**Implication pratique** : un `--check` qui sort `changed=0` partout = rien à appliquer.
C'est l'**état stationnaire** que vous voulez voir en CI avant un merge sur `main`.

## 📚 Exercice 4 — `check_mode: false` pour les tâches qui ont besoin de tourner

Certaines tâches **doivent s'exécuter** même en `--check`, parce qu'elles produisent
une **information** (pas un changement). Exemple typique : récupérer la version
d'un binaire avec `command:`.

Modifiez `lab.yml` :

```yaml
---
- name: Lab checkmode - exercice 4
  hosts: web1.lab
  become: true
  tasks:
    - name: Recuperer la version d openssl (toujours executer)
      ansible.builtin.command: openssl version
      register: openssl_version
      check_mode: false
      changed_when: false

    - name: Afficher la version
      ansible.builtin.debug:
        var: openssl_version.stdout

    - name: Poser un MOTD avec la version d openssl
      ansible.builtin.copy:
        dest: /etc/motd
        content: "Web1 — openssl: {{ openssl_version.stdout }}\n"
        mode: "0644"
```

**Lancer en `--check`** :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation** :

- La tâche `command: openssl version` **s'exécute pour de vrai** (vous voyez la version dans le `debug:`).
- La tâche `copy:` **simule** l'écriture mais n'écrit pas.
- Le `--diff` montre la nouvelle valeur du MOTD avec la version d'openssl interpolée.

**Sans `check_mode: false`** sur la tâche `command:`, Ansible aurait **skippé** la
récupération de la version (et la suite du playbook aurait planté avec
`'openssl_version' is undefined` ou un MOTD bizarre).

## 📚 Exercice 5 — Le piège : modules qui ne supportent pas `--check`

Tous les modules **ne supportent pas** `--check` correctement. Pour les modules
non-supportés, Ansible affiche un warning et **skip** la tâche en mode check.

Ajoutez à `lab.yml` :

```yaml
    - name: Tache non check-aware (exemple shell)
      ansible.builtin.shell: |
        echo "Hello from shell" >> /tmp/lab-shell-output.txt
```

**Relancez en `--check`** :

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check
```

🔍 **Observation** : la tâche `shell:` est marquée **`skipped`** (pas `changed`), avec
un warning du genre `Skipping... unable to check_mode`. Ansible n'a aucun moyen de
deviner ce que votre commande shell ferait — donc il refuse de simuler.

**Conséquence** : en `--check`, vous n'obtenez **pas** de garantie que tout le playbook
se déroulera bien. Les tâches `shell:` / `command:` non check-aware sont des **angles
morts**. À mitiger en :

- préférant des **modules dédiés** (`copy:`, `template:`, `lineinfile:`) qui sont check-aware ;
- ajoutant `check_mode: false` + `changed_when: ...` pour forcer l'exécution lecture-seule.

## 🔍 Observations à noter

Avant de passer au challenge, vérifiez que vous comprenez :

- **`--check` ne modifie rien**, mais le `PLAY RECAP` peut afficher `changed=N` (intention de changement).
- **`--diff` est l'outil de revue** : c'est ce qui apparaît dans une PR de change management.
- **`changed=0` en `--check`** = état stationnaire, rien à faire en production.
- **`check_mode: false`** force l'exécution d'une tâche en mode check (utile pour les tâches lecture-seule).
- **`shell:` / `command:`** sont des angles morts du `--check` sauf si vous les rendez explicitement check-aware.

## 🤔 Questions de réflexion

1. Vous avez un playbook qui modifie une config nginx. Vous voulez **valider la syntaxe**
   nginx avant de redéployer (via `nginx -t`). Comment articulez-vous `--check`,
   `check_mode: false`, et `validate:` du module `template:` pour avoir une garantie
   complète ?

2. Pourquoi un run en `--check` peut-il afficher `changed=1` alors qu'un run réel
   immédiatement après affichera `changed=0` ? Donnez **deux causes** possibles.

3. Dans une CI, vous lancez `ansible-playbook --check --diff` sur chaque PR. Quel
   **exit code** d'`ansible-playbook` retourne-t-il quand `changed > 0` en `--check` ?
   Faut-il **fail la CI** dans ce cas ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Hooks de validation** : combinez `validate:` du module `template:` avec `--check`
  pour échouer un dry-run si la config générée est syntaxiquement invalide
  (`validate: 'nginx -t -c %s'`).
- **`--start-at-task`** : reprendre un playbook après une tâche échouée — utile
  combiné à `--check` pour valider la suite avant de re-jouer.
- **Le pattern `audit-only`** : un play qui ne fait que des `command: changed_when: false`
  pour collecter de l'info sans rien modifier. Tourne bien en `--check` car aucune
  tâche n'est censée modifier l'état.
- **`ANSIBLE_DIFF_ALWAYS=1`** : variable d'env pour activer `--diff` par défaut
  sans le passer à chaque commande. Utile en dev local.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/checkmode-diff/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/checkmode-diff/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/checkmode-diff/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
