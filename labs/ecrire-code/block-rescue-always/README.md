# Lab 23 — `block:` / `rescue:` / `always:` (try / catch / finally)

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

🔗 [**Block / rescue / always Ansible : try/catch/finally**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/block-rescue-always/)

`block:` regroupe plusieurs tâches sous une **structure de gestion d'erreurs** :

- **`block:`** = liste de tâches à essayer (équivalent du `try`).
- **`rescue:`** = liste de tâches exécutées **si une tâche du block échoue** (`catch`).
- **`always:`** = liste de tâches **toujours** exécutées, succès ou échec (`finally`).

Cette structure est essentielle pour les **opérations transactionnelles** : déployer
une nouvelle release, sauvegarder en cas d'échec, nettoyer un fichier temporaire.
Sans `block/rescue`, un `failed_when` peut casser le play entier — avec
`block/rescue`, on rattrape proprement.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Grouper** plusieurs tâches dans un `block:`.
2. **Capturer** une erreur avec `rescue:` et **agir** (rollback, notification, log).
3. **Garantir** un nettoyage avec `always:`.
4. **Utiliser** `ansible_failed_task` et `ansible_failed_result` dans `rescue:`.
5. **Imbriquer** des blocks pour des structures try/catch/finally complexes.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/block-*.txt"
```

## 📚 Exercice 1 — Block sans erreur (cas nominal)

Créez `lab.yml` :

```yaml
---
- name: Demo block sans erreur
  hosts: db1.lab
  become: true
  tasks:
    - name: Block transactionnel
      block:
        - name: Tache 1 - Marquer le debut
          ansible.builtin.copy:
            content: "Start at {{ ansible_date_time.iso8601 }}\n"
            dest: /tmp/block-start.txt
            mode: "0644"

        - name: Tache 2 - Operation principale
          ansible.builtin.copy:
            content: "Main operation OK\n"
            dest: /tmp/block-main.txt
            mode: "0644"

      rescue:
        - name: Rescue (ne devrait PAS tourner ici)
          ansible.builtin.copy:
            content: "Erreur capturee !\n"
            dest: /tmp/block-rescue.txt
            mode: "0644"

      always:
        - name: Always - cleanup
          ansible.builtin.copy:
            content: "Cleanup at {{ ansible_date_time.iso8601 }}\n"
            dest: /tmp/block-cleanup.txt
            mode: "0644"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation** : sortie console :

```
TASK [Tache 1 - Marquer le debut] : ok / changed
TASK [Tache 2 - Operation principale] : ok / changed
TASK [Always - cleanup] : ok / changed
```

**`rescue:` n'est pas exécuté**. **`always:` est exécuté**. Sur db1 :

```bash
ssh ansible@db1.lab 'ls /tmp/block-*.txt'
# block-cleanup.txt, block-main.txt, block-start.txt — PAS block-rescue.txt
```

## 📚 Exercice 2 — Block avec erreur (déclenchement de `rescue:`)

Modifiez la **Tâche 2** pour qu'elle échoue :

```yaml
- name: Tache 2 - Operation qui plante
  ansible.builtin.dnf:
    name: paquet-inexistant-12345
    state: present
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation** : sortie console :

```
TASK [Tache 1 - Marquer le debut] : ok / changed
TASK [Tache 2 - Operation qui plante] : FAILED!
TASK [Rescue ...] : ok / changed
TASK [Always - cleanup] : ok / changed
```

**`rescue:` est exécuté** (la tâche 2 a échoué). **`always:` est exécuté aussi**.
Le **PLAY RECAP** affiche `failed=0` car le `rescue:` a **rattrapé** l'erreur — le
play se termine **avec succès**.

C'est l'**équivalent du `try/except` Python** : sans `rescue:`, la tâche 2 aurait
fait `failed=1` et arrêté le play.

## 📚 Exercice 3 — Variables magiques dans `rescue:`

Dans `rescue:`, Ansible expose **deux variables** très utiles :

- **`ansible_failed_task`** : le dict de la tâche qui a échoué (`name`, `action`, ...).
- **`ansible_failed_result`** : le résultat de la tâche (msg, rc, stderr, ...).

```yaml
rescue:
  - name: Diagnostiquer l erreur
    ansible.builtin.copy:
      dest: /tmp/block-rescue-diagnostic.txt
      mode: "0644"
      content: |
        Tache echouee : {{ ansible_failed_task.name }}
        Module : {{ ansible_failed_task.action }}
        Message : {{ ansible_failed_result.msg | default('inconnu') }}
        Stderr : {{ ansible_failed_result.stderr | default('') }}

  - name: Notifier (simulation)
    ansible.builtin.debug:
      msg: "ALERTE : tache '{{ ansible_failed_task.name }}' a echoue sur {{ inventory_hostname }}"
```

🔍 **Observation** : ces variables permettent un **rescue ciblé** — log précis,
notification structurée, branchement conditionnel selon l'erreur.

## 📚 Exercice 4 — `always:` pour cleanup transactionnel

Pattern classique : créer un fichier temporaire, faire l'opération, **toujours**
le supprimer (succès ou échec).

```yaml
- name: Operation transactionnelle avec cleanup garanti
  hosts: db1.lab
  become: true
  tasks:
    - name: Block transactionnel avec cleanup
      block:
        - name: Creer un fichier de lock
          ansible.builtin.copy:
            content: "PID {{ ansible_date_time.epoch }}\n"
            dest: /tmp/block-lock.txt
            mode: "0644"

        - name: Operation critique (peut echouer)
          ansible.builtin.command: /bin/false
          # Tache qui plante volontairement

      rescue:
        - name: Logger l echec
          ansible.builtin.copy:
            content: "Echec rattrape\n"
            dest: /tmp/block-fail-log.txt
            mode: "0644"

      always:
        - name: Toujours supprimer le lock
          ansible.builtin.file:
            path: /tmp/block-lock.txt
            state: absent
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation** : `block-lock.txt` est **créé puis supprimé**. Même si l'opération
critique échoue, le lock est nettoyé. C'est le **pattern transactionnel** essentiel
pour éviter les locks orphelins.

## 📚 Exercice 5 — Block imbriqué (try / catch / finally complexe)

```yaml
- name: Block externe
  block:
    - name: Block interne 1
      block:
        - name: Operation interne
          ansible.builtin.command: /bin/false
      rescue:
        - name: Rescue interne
          ansible.builtin.debug:
            msg: "Rescue interne capture"

    - name: Tache apres le rescue interne
      ansible.builtin.debug:
        msg: "Cette tache tourne car le rescue interne a rattrape"

  rescue:
    - name: Rescue externe (ne devrait PAS tourner)
      ansible.builtin.debug:
        msg: "Rescue externe"

  always:
    - name: Always externe
      ansible.builtin.debug:
        msg: "Always externe"
```

🔍 **Observation** : le **rescue interne** rattrape l'erreur, donc le **rescue externe
n'est pas déclenché**. Pattern utile pour des **fallbacks en cascade** : essayer A,
si A échoue essayer B, si B échoue alors notifier.

## 📚 Exercice 6 — Le piège : `rescue:` qui plante aussi

Si une tâche du `rescue:` **plante elle-même**, le `rescue` ne rattrape **pas**
sa propre erreur — le play s'arrête.

```yaml
- name: Demo piege rescue qui plante
  block:
    - ansible.builtin.command: /bin/false  # Tache 1 plante

  rescue:
    - ansible.builtin.command: /bin/false  # Rescue plante aussi

  always:
    - ansible.builtin.debug:
        msg: "Always tourne quand meme"
```

🔍 **Observation** : le **rescue plante**, le **always tourne quand même**, mais le
PLAY RECAP affiche `failed=1`. Le play est en échec. Le rescue ne **rattrape pas
sa propre erreur**.

**Bonne pratique** : un `rescue:` doit être **simple et fiable** (une notification,
un log, un cleanup) — ne pas y mettre des opérations qui peuvent elles-mêmes échouer.

## 🔍 Observations à noter

- **`block:`** = try, **`rescue:`** = catch, **`always:`** = finally.
- **`rescue:` rattrape les erreurs** du block et empêche le play d'échouer.
- **`always:`** s'exécute **toujours**, succès ou échec.
- **`ansible_failed_task` / `ansible_failed_result`** = variables magiques dans `rescue:`.
- **Blocks imbriqués** = fallbacks en cascade.
- **`rescue:` qui plante** ne rattrape pas sa propre erreur — le `always:` tourne mais le play échoue.

## 🤔 Questions de réflexion

1. Vous voulez **déployer une release** avec rollback automatique en cas d'échec.
   Comment articulez-vous `block:` (déployer), `rescue:` (rollback), et `always:`
   (notification) ?

2. Quelle est la différence sémantique entre `ignore_errors: true` (tâche unique)
   et `block: + rescue:` (groupe de tâches) ? Quand préférer l'un ou l'autre ?

3. Un `rescue:` peut **modifier** des variables avec `set_fact`. Comment vérifier
   après le block si la run est passée par le `rescue:` (pour conditionner une tâche
   ultérieure) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`when:` sur un block** : conditionne le block entier — équivalent à mettre
  `when:` sur chaque tâche, mais DRY.
- **`tags:` sur un block** : applique le tag à toutes les tâches du block. Utile
  pour des sections "deploy" / "rollback" / "verify" tagguées.
- **`become:` sur un block** : élève les droits pour toutes les tâches du block —
  plus propre que de répéter `become: true` sur chaque tâche.
- **Pattern saga** : enchaîner plusieurs blocks transactionnels avec leur propre
  rescue. Si l'un échoue, déclencher les compensations des précédents (rollback en
  cascade).
- **Lab 25 (`ignore_errors`)** : alternative plus simple quand on veut juste **ne
  pas planter** sans gérer le rattrapage.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/block-rescue-always/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/block-rescue-always/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/block-rescue-always/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
