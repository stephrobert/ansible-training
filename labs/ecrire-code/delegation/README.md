# Lab 11 — Délégation (`delegate_to`, `run_once`, `local_action`)

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

🔗 [**Délégation Ansible : delegate_to, run_once, local_action**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/)

`delegate_to:` redirige l'exécution d'une tâche vers **un autre hôte** que celui ciblé
par le play. `run_once: true` exécute la tâche **une seule fois** (sur le premier hôte
du batch, ou sur l'hôte délégué). `local_action:` est un raccourci pour
`delegate_to: localhost`. Ces 3 outils sont la **base des patterns multi-hôtes** :
notifier un load-balancer externe, créer un DNS record, mettre une machine en
maintenance, déclencher un backup centralisé.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Rediriger** une tâche vers un autre managed node via `delegate_to:`.
2. **Exécuter** une tâche **une seule fois** dans un play multi-hôtes (`run_once`).
3. **Combiner** `delegate_to + run_once` pour les patterns notification.
4. **Utiliser** `local_action:` pour les opérations côté control node.
5. **Distinguer** `delegate_facts: true` de `delegate_to:` simple.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ping
ansible db1.lab -m ping
# Tous doivent etre en SUCCESS
```

Nettoyer les marqueurs des runs précédents :

```bash
ansible all -b -m file -a "path=/tmp/delegated-from-webservers.txt state=absent"
ansible all -b -m file -a "path=/tmp/local-action-marker.txt state=absent"
```

## 📚 Exercice 1 — `delegate_to:` simple (sans `run_once`)

Créez `lab.yml` :

```yaml
---
- name: Demo delegate_to (sans run_once)
  hosts: webservers
  become: true
  tasks:
    - name: Annoncer chaque webserver sur db1
      ansible.builtin.copy:
        dest: "/tmp/announce-{{ inventory_hostname }}.txt"
        content: "Webserver {{ inventory_hostname }} ({{ ansible_default_ipv4.address }}) en service\n"
        mode: "0644"
      delegate_to: db1.lab
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/delegation/lab.yml
```

🔍 **Observation** : la tâche tourne **sur db1.lab** (pas sur web1/web2), mais **2 fois**
(une par webserver), créant 2 fichiers `/tmp/announce-web1.lab.txt` et
`/tmp/announce-web2.lab.txt` sur db1.

```bash
ssh ansible@db1.lab 'ls /tmp/announce-*.txt'
```

**Variables** : `inventory_hostname` reste celui du **boucle** (web1, puis web2), pas
de db1. C'est la subtilité — la tâche **s'exécute** sur db1 mais voit les vars de
l'hôte courant du play.

## 📚 Exercice 2 — `delegate_to + run_once`

Modifiez `lab.yml` :

```yaml
---
- name: Demo delegate_to + run_once
  hosts: webservers
  become: true
  tasks:
    - name: Notifier la DB une seule fois
      ansible.builtin.copy:
        dest: /tmp/delegated-from-webservers.txt
        content: "Deploy webservers OK, declenche par {{ inventory_hostname }} a {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"
      delegate_to: db1.lab
      run_once: true
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/delegation/lab.yml
```

🔍 **Observation** : un **seul** fichier `/tmp/delegated-from-webservers.txt` sur db1,
contenant le **premier webserver** du play (web1.lab par ordre alphabétique). C'est
le pattern **notification "fin de déploiement"** : on prévient db1 quand TOUTE la
flotte web a été déployée, pas une fois par webserver.

```bash
ssh ansible@db1.lab 'cat /tmp/delegated-from-webservers.txt'
```

## 📚 Exercice 3 — `local_action:` (raccourci pour control node)

Pour exécuter une tâche **côté control node** (votre machine), `local_action:` est
plus court que `delegate_to: localhost`.

```yaml
---
- name: Log local apres deploy
  hosts: webservers
  tasks:
    - name: Marquer le deploy dans un log local
      local_action:
        module: ansible.builtin.copy
        content: "Deploy {{ inventory_hostname }} OK a {{ ansible_date_time.iso8601 }}\n"
        dest: "/tmp/local-action-marker-{{ inventory_hostname }}.txt"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/delegation/lab-localaction.yml
ls /tmp/local-action-marker-*.txt
```

🔍 **Observation** : 2 fichiers sont créés **sur votre machine locale** (pas sur web1/web2).
`local_action:` est strictement équivalent à `delegate_to: localhost` mais s'écrit en
moins de lignes.

**Note** : pas de `become:` automatique avec `local_action:` — pour écrire dans `/etc/`
côté local, il faut quand même `become: true`.

## 📚 Exercice 4 — `delegate_facts: true` (capture des facts d'un autre hôte)

Cas d'usage : votre play tourne sur les `webservers`, mais vous avez besoin de **lire
les facts de db1** (pour récupérer son IP, sa version OS, etc.).

```yaml
---
- name: Pre-collecter les facts de db1
  hosts: webservers
  tasks:
    - name: Gather facts de db1.lab
      ansible.builtin.setup:
      delegate_to: db1.lab
      delegate_facts: true
      run_once: true

    - name: Utiliser ces facts cote webserver
      ansible.builtin.debug:
        msg: |
          Webserver {{ inventory_hostname }} pourra parler a db1
          IP db1 : {{ hostvars['db1.lab'].ansible_default_ipv4.address }}
          OS db1 : {{ hostvars['db1.lab'].ansible_distribution }}
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/delegation/lab-delegate-facts.yml
```

🔍 **Observation** :

- **Sans `delegate_facts: true`**, les facts collectés iraient dans
  `hostvars['web1.lab'].ansible_*` (faux !) parce que le play tourne sur web1.
- **Avec `delegate_facts: true`**, les facts vont dans `hostvars['db1.lab'].ansible_*`
  (correct).

**Sans cette option**, vous avez le piège classique : les facts sont rangés sous le
mauvais hostname et vous référencez la mauvaise machine partout.

## 📚 Exercice 5 — Le piège classique : `run_once` + `serial:`

`run_once: true` s'exécute **une seule fois par batch** quand `serial:` est défini.
Si `serial: 1`, vous avez `N` batches → `run_once` tourne **N fois** au total !

Créez `lab-piege.yml` :

```yaml
---
- name: Demo piege run_once + serial
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Cense ne tourner qu une fois (piege !)
      ansible.builtin.shell: |
        echo "Iteration a {{ ansible_date_time.iso8601 }}" >> /tmp/run-once-trap.txt
      delegate_to: db1.lab
      run_once: true
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/ecrire-code/delegation/lab-piege.yml
ssh ansible@db1.lab 'cat /tmp/run-once-trap.txt'
```

🔍 **Observation** : le fichier contient **2 lignes** (une par batch web1, puis web2),
**pas 1** comme attendu. `run_once` est local au batch, pas global au play.

**Solution** : si vous voulez vraiment **une seule fois pour tout le play**, faire
le `delegate_to + run_once` dans un **play séparé** sans `serial:`, ou conditionner
avec `when: inventory_hostname == ansible_play_hosts_all[0]`.

## 🔍 Observations à noter

- **`delegate_to: <host>`** = la tâche **s'exécute** sur cet hôte, mais **voit** les vars de l'hôte du play.
- **`run_once: true`** = la tâche tourne **une seule fois par batch** (pas par play).
- **`local_action:`** = raccourci pour `delegate_to: localhost`.
- **`delegate_facts: true`** = les facts collectés sont rangés sous l'hôte délégué (pas l'hôte du play).
- **Combinaison `delegate_to + run_once`** = pattern notification (load-balancer, DNS, monitoring).

## 🤔 Questions de réflexion

1. Vous déployez sur 50 webservers. Avant de redémarrer chaque webserver, vous voulez
   le **retirer du load-balancer** (HAProxy sur lb1.lab). Comment articulez-vous
   `delegate_to`, `serial: 1`, et le pattern pre/post tasks ?

2. `delegate_to: db1.lab` sur une tâche `command:` qui crée `/etc/myapp.conf` — quel
   est le **piège de variables** classique ? (indice : `inventory_hostname` est-il celui
   de db1 ou du host courant du play ?)

3. Pourquoi `run_once: true` sans `delegate_to:` peut surprendre dans un play
   multi-hôtes ? (Sur quel hôte la tâche tourne-t-elle ?)

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Pattern blue/green** : `delegate_to: load-balancer.lab` + `run_once: true` pour
  basculer le trafic sur la nouvelle release.
- **Pattern DNS dynamique** : créer un record DNS via `delegate_to: dns.lab` et
  l'API Bind/PowerDNS.
- **`delegate_to: 127.0.0.1`** vs **`delegate_to: localhost`** : différence subtile
  — `127.0.0.1` force une connexion SSH locale, `localhost` utilise le **connection
  plugin local** (sans SSH). Préférer `localhost` (plus rapide).
- **`add_host:` + `delegate_to:`** : pattern d'inventaire dynamique. Créer un host
  à la volée puis lui déléguer une tâche.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/delegation/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/delegation/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/delegation/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
