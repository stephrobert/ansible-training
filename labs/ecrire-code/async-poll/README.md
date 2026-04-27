# Lab 10 — Async et poll (tâches longues sans bloquer SSH)

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

🔗 [**Async et poll Ansible : tâches longues, fire-and-forget, async_status**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/)

Par défaut, Ansible **maintient une connexion SSH ouverte** pendant toute la durée
d'une tâche. Si la tâche dure 30 minutes, vous risquez un **timeout SSH** (réseau qui
coupe, firewall qui kill les connexions inactives) — Ansible perd alors la sortie et
considère la tâche comme **failed** alors qu'elle continue côté managed node.

`async:` détache la tâche du process Ansible et **libère la connexion SSH**.
`poll:` contrôle si Ansible attend (`> 0`) ou non (`0` = fire-and-forget). Pour
récupérer le résultat plus tard, `async_status:` interroge le **job ID**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Détacher** une tâche longue avec `async + poll: 0` (fire-and-forget).
2. **Récupérer** le résultat plus tard via `async_status: jid:`.
3. **Combiner** `async:` avec `until:` pour faire du polling actif.
4. **Diagnostiquer** un job orphelin (le process est parti, mais on a perdu le `jid`).
5. **Choisir** entre `async + poll > 0` (sync avec heartbeat) et `async + poll: 0` (vraiment async).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
```

## 📚 Exercice 1 — Le problème : tâche longue qui timeout

Pour comprendre l'utilité d'`async`, observez d'abord ce qui se passe **sans** lui.
Créez `lab-blocking.yml` :

```yaml
---
- name: Tache longue sans async (problematique)
  hosts: web1.lab
  become: true
  tasks:
    - name: Sleep 5 secondes
      ansible.builtin.command: sleep 5
```

**Lancez et chronométrez** :

```bash
time ansible-playbook labs/ecrire-code/async-poll/lab-blocking.yml
```

🔍 **Observation** : le play prend **5+ secondes** à finir, et la connexion SSH reste
**ouverte** tout du long. Sur un sleep de 5s pas de problème — sur une tâche de 30
minutes via VPN qui coupe les sessions inactives à 5 min, c'est un drame.

## 📚 Exercice 2 — Async avec `poll: 0` (fire-and-forget)

Créez `lab-async.yml` :

```yaml
---
- name: Demo async + async_status
  hosts: web1.lab
  become: true
  tasks:
    - name: Lancer sleep 8 en background (fire-and-forget)
      ansible.builtin.command: sleep 8
      async: 30      # Timeout cote managed node
      poll: 0        # Ne pas bloquer Ansible
      register: sleep_job

    - name: Afficher le job ID retenu
      ansible.builtin.debug:
        msg: "Job lance avec ID {{ sleep_job.ansible_job_id }}"

    - name: Attendre la fin du job async
      ansible.builtin.async_status:
        jid: "{{ sleep_job.ansible_job_id }}"
      register: job_result
      until: job_result.finished
      retries: 15
      delay: 2

    - name: Afficher le statut final
      ansible.builtin.debug:
        msg: "Job {{ sleep_job.ansible_job_id }} fini en {{ job_result.delta }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/async-poll/lab-async.yml
```

🔍 **Observation** :

- La tâche `Lancer sleep 8` retourne **immédiatement** (la connexion SSH se referme).
- `async_status` polle toutes les 2 secondes (`delay: 2`) jusqu'à 15 fois (`retries: 15` = max 30s).
- Quand le sleep finit côté managed node, `async_status` retourne `finished: 1`.

**Pourquoi pas juste `poll > 0` ?** Avec `async: 30` et `poll: 5`, Ansible polle
**tous les 5 secondes** mais **garde la connexion ouverte** entre deux polls. Idéal
pour des tâches **moyennes** (10-60s). Avec `poll: 0`, la connexion est **fermée
immédiatement** — idéal pour les tâches **vraiment longues** (>5min).

## 📚 Exercice 3 — Plusieurs jobs en parallèle sur le même hôte

`async + poll: 0` permet de **lancer N jobs concurrents** sur un même hôte. Très utile
pour, par exemple, paralléliser plusieurs commandes `dnf install` ou des
téléchargements multi-fichiers.

Créez `lab-parallel.yml` :

```yaml
---
- name: Lancer 3 jobs en parallele
  hosts: web1.lab
  become: true
  tasks:
    - name: Job 1 - sleep 4
      ansible.builtin.command: sleep 4
      async: 30
      poll: 0
      register: job1

    - name: Job 2 - sleep 6
      ansible.builtin.command: sleep 6
      async: 30
      poll: 0
      register: job2

    - name: Job 3 - sleep 8
      ansible.builtin.command: sleep 8
      async: 30
      poll: 0
      register: job3

    - name: Attendre la fin des 3 jobs
      ansible.builtin.async_status:
        jid: "{{ item }}"
      register: jobs_result
      until: jobs_result.finished
      retries: 20
      delay: 1
      loop:
        - "{{ job1.ansible_job_id }}"
        - "{{ job2.ansible_job_id }}"
        - "{{ job3.ansible_job_id }}"
```

**Lancez et chronométrez** :

```bash
time ansible-playbook labs/ecrire-code/async-poll/lab-parallel.yml
```

🔍 **Observation** : le play total prend ~**8 secondes** (la durée du job le plus long),
pas 4+6+8 = 18s. Les 3 jobs ont tourné **en parallèle** côté managed node.

## 📚 Exercice 4 — Le piège : `async: <T>` plus court que la tâche

Modifiez l'exercice 2 pour que `async: 5` mais que le sleep soit `sleep 8` :

```yaml
- name: Lancer sleep 8 avec async timeout 5
  ansible.builtin.command: sleep 8
  async: 5    # Timeout cote managed node — INSUFFISANT
  poll: 0
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/async-poll/lab-async.yml
```

🔍 **Observation** : `async_status` finit par retourner `finished: 1` MAIS avec un
**`failed: 1`** et un message `async task did not complete within the requested time`.

C'est le **timeout côté managed node** : Ansible (en réalité, le helper `async_wrapper`)
**kill** le process si la tâche dépasse `async:` secondes.

**Règle** : `async:` doit être **toujours plus grand** que la durée maximale attendue
de la tâche, avec une marge généreuse (×2 ou ×3).

## 📚 Exercice 5 — Job orphelin (vraie fire-and-forget)

`async + poll: 0` **sans** `async_status:` lance un job que vous **n'attendez jamais**.
Pratique pour déclencher quelque chose dont le résultat ne vous intéresse pas dans
ce play (notification, push de métriques, etc.).

```yaml
- name: Notifier Slack en arriere-plan (on s en fout du resultat)
  ansible.builtin.command: |
    curl -X POST -H 'Content-type: application/json'
    --data '{"text":"deploy done on {{ inventory_hostname }}"}'
    https://hooks.slack.com/services/...
  async: 60
  poll: 0
  changed_when: false
```

🔍 **Observation** : Ansible **ne sait pas** si le curl a réussi. Si l'API Slack est
down, vous perdez la notification mais le deploy continue. C'est **acceptable** pour
des notifications best-effort.

**Attention** : pour une **opération critique** (insertion en base, génération de
backup), ne **jamais** faire fire-and-forget sans `async_status:` — vous perdez la
visibilité d'erreurs.

## 🔍 Observations à noter

- **`async: <secondes>`** = timeout côté managed node (kill si dépassé).
- **`poll: 0`** = fire-and-forget, connexion SSH refermée immédiatement.
- **`poll: > 0`** = sync avec heartbeat tous les N secondes (connexion ouverte mais légère).
- **`async_status:` + `jid:`** = récupération du résultat (à utiliser avec `until: finished`).
- **Plusieurs jobs en parallèle sur un même hôte** = pattern de **parallélisation locale**.
- **`async:` doit être > durée max** sinon le job est tué prématurément.

## 🤔 Questions de réflexion

1. Vous voulez lancer un `dnf upgrade` qui peut prendre 30 min. Vous êtes derrière
   un VPN qui coupe les sessions inactives à 10 min. Quelle config `async + poll`
   utilisez-vous, et pourquoi ne pas simplement augmenter le timeout SSH ?

2. Un collègue met `poll: 0` partout "pour aller plus vite". Il ne capture pas le
   `jid` et ne fait pas d'`async_status`. Quel est le risque concret ?

3. Sur 100 hôtes, vous voulez lancer un download long (5 min) en parallèle. Pourquoi
   `async + poll: 0` est plus efficace que `forks: 100` avec un `command:` synchrone ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`async: 0` + `poll: 0`** : combinaison **interdite** (Ansible refuse). `async`
  doit toujours avoir une valeur > 0.
- **Le helper `async_wrapper`** : Ansible copie un script Python sur le managed
  node qui supervise la tâche. Si vous tuez le wrapper (`pkill async_wrapper`),
  vous perdez le `jid` (job orphelin réel).
- **`mode: cleanup`** sur `async_status:` : nettoie les fichiers temporaires côté
  managed node. À utiliser dans un play de **maintenance** si vous accumulez des
  status files dans `~/.ansible_async/`.
- **Combinaison `async + retries + delay`** : pattern de **wait-for-condition**
  beaucoup plus efficace que `wait_for:` quand la condition se résume à
  "ce job s'est terminé proprement".

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/async-poll/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/async-poll/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/async-poll/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
