# Lab 16 — `register:` et `set_fact:` (capture et création de variables)

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

🔗 [**register et set_fact Ansible : capture, durée de vie, cacheable**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/register-set-fact/)

`register: var` capture le résultat d'un module dans une variable (`rc`, `stdout`,
`stderr`, `changed`, `failed`, plus des champs spécifiques au module). `set_fact:`
crée ou recalcule une variable au runtime — niveau 18 dans la précédence (donc bat
`vars:` du play). Ces deux mécanismes sont la **base du pattern "tâche → décision"**
en Ansible : exécuter, observer, agir selon le résultat.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Capturer** la sortie d'un module avec `register:` et explorer sa structure.
2. **Réutiliser** un champ capturé dans une tâche suivante (`when:`, `loop:`).
3. **Créer** une variable au runtime via `set_fact:` à partir d'une logique de filtrage.
4. **Persister** un fact via `cacheable: true` pour les runs ultérieurs.
5. **Distinguer** la portée et la durée de vie de `register:` vs `set_fact:`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/register-*.txt /tmp/setfact-*.txt"
```

## 📚 Exercice 1 — `register:` simple sur `command:`

Créez `lab.yml` :

```yaml
---
- name: Demo register simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Capturer la version d openssl
      ansible.builtin.command: openssl version
      register: ssl_result
      changed_when: false

    - name: Inspecter la structure complete de la variable register
      ansible.builtin.debug:
        var: ssl_result

    - name: Utiliser uniquement le stdout
      ansible.builtin.debug:
        msg: "openssl version : {{ ssl_result.stdout }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/register-set-fact/lab.yml
```

🔍 **Observation** : la première `debug: var: ssl_result` montre **toute la structure**
retournée par le module :

```yaml
ssl_result:
  cmd: ['openssl', 'version']
  rc: 0
  stdout: "OpenSSL 3.x.x ..."
  stdout_lines: ['OpenSSL 3.x.x ...']
  stderr: ""
  start: "..."
  end: "..."
  delta: "0:00:00.012345"
  failed: false
  changed: false
```

**Champs les plus utiles** :

- **`rc`** : code retour du process (0 = succès).
- **`stdout`** / **`stdout_lines`** : sortie brute / liste de lignes.
- **`failed`** / **`changed`** : statuts de la tâche.
- **`delta`** : durée d'exécution.

## 📚 Exercice 2 — Conditionner sur `register:`

```yaml
- name: Tester si /etc/passwd existe
  ansible.builtin.stat:
    path: /etc/passwd
  register: passwd_stat

- name: Action si le fichier existe et est non vide
  ansible.builtin.copy:
    content: "passwd existe, taille {{ passwd_stat.stat.size }} octets\n"
    dest: /tmp/register-passwd-stat.txt
    mode: "0644"
  when: passwd_stat.stat.exists and passwd_stat.stat.size > 0
```

🔍 **Observation** : `stat:` est le module de **diagnostic** par excellence — utilisé
en duo avec `register:` + `when:`, il permet de coder des **branches conditionnelles**
robustes.

**Champs courants de `stat:`** :

- `passwd_stat.stat.exists` (bool)
- `passwd_stat.stat.isfile` / `passwd_stat.stat.isdir` / `passwd_stat.stat.islnk`
- `passwd_stat.stat.size` (octets)
- `passwd_stat.stat.mode` (string octal `'0644'`)
- `passwd_stat.stat.checksum` (SHA1 du contenu, si fichier)

## 📚 Exercice 3 — `register:` + `loop:` (capture multi-itération)

```yaml
- name: Tester plusieurs services
  ansible.builtin.systemd_service:
    name: "{{ item }}"
  register: services_status
  loop:
    - sshd
    - chronyd
    - rsyslog
  changed_when: false
  failed_when: false

- name: Inspecter la structure (liste de results)
  ansible.builtin.debug:
    var: services_status.results | map(attribute='name') | list

- name: Extraire ceux qui sont active
  ansible.builtin.debug:
    msg: "Active : {{ services_status.results | selectattr('status.ActiveState', 'equalto', 'active') | map(attribute='name') | list }}"
```

🔍 **Observation** : avec `loop:`, `register:` capture **une liste** sous `.results`.
Chaque élément contient le résultat de l'itération + la valeur de `item`. Pour
extraire un sous-ensemble, le filtre `selectattr` est l'outil naturel.

## 📚 Exercice 4 — `set_fact:` (création de variable au runtime)

`set_fact` est utile pour **calculer** une variable à partir de plusieurs sources.

```yaml
- name: Calculer le mode de deploy selon l environnement
  ansible.builtin.set_fact:
    deploy_mode: >-
      {% if ansible_distribution_major_version | int >= 9 %}
      modern
      {% else %}
      legacy
      {% endif %}

- name: Calculer le label en concatenant
  ansible.builtin.set_fact:
    deploy_label: "{{ inventory_hostname }}-{{ ansible_date_time.epoch }}"

- name: Utiliser les facts crees
  ansible.builtin.copy:
    content: |
      Mode : {{ deploy_mode | trim }}
      Label : {{ deploy_label }}
    dest: /tmp/setfact-marker.txt
    mode: "0644"
```

🔍 **Observation** : `set_fact:` crée une variable **immédiatement disponible** dans
les tâches suivantes du même play. Différence majeure avec `vars:` : la valeur peut
être **calculée** (concaténation, condition, filtres).

**Niveau de précédence** : 18 — `set_fact` bat `vars:` du play (14) et tous les
group_vars/host_vars. Pratique pour **forcer** une valeur calculée.

## 📚 Exercice 5 — `cacheable: true` (persister entre runs)

Si `fact_caching = jsonfile` est configuré dans `ansible.cfg`, vous pouvez **persister**
un fact créé par `set_fact` :

```yaml
- name: Set fact persistant
  ansible.builtin.set_fact:
    last_deploy_label: "{{ inventory_hostname }}-{{ ansible_date_time.epoch }}"
    cacheable: true
```

**Lancer le playbook une fois**, puis **un second playbook** qui ne ferait que :

```yaml
- name: Lire le fact precedent
  ansible.builtin.debug:
    var: last_deploy_label
```

🔍 **Observation** : si `cacheable: true` était présent au premier run et le fact
caching activé, la valeur **survit** au second run, **sans regather de facts**.

**Inspecter le cache** :

```bash
ls .ansible_facts/  # Defini dans ansible.cfg : fact_caching_connection
cat .ansible_facts/s1_db1.lab | python3 -m json.tool | grep last_deploy
```

## 📚 Exercice 6 — Le piège : `register:` en boucle, accès direct

Erreur classique : tenter d'accéder à `myreg.stdout` après une boucle, en oubliant
que `register` retourne une **liste** sous `.results`.

```yaml
- name: Boucle qui capture
  ansible.builtin.command: "echo {{ item }}"
  loop: [a, b, c]
  register: outputs
  changed_when: false

- name: Erreur typique (ne fait que prendre la derniere)
  ansible.builtin.debug:
    msg: "stdout : {{ outputs.stdout | default('absent') }}"

- name: Forme correcte
  ansible.builtin.debug:
    msg: "stdouts : {{ outputs.results | map(attribute='stdout') | list }}"
```

🔍 **Observation** : `outputs.stdout` est `absent` (la clé n'existe pas au niveau
racine quand il y a `loop:`). La forme correcte passe par **`.results`** + `map`.

## 🔍 Observations à noter

- **`register:`** capture le résultat d'**un module** sous une variable (rc, stdout, stderr, custom).
- **Avec `loop:`**, `register:` retourne une **liste** sous `.results`.
- **`set_fact:`** crée une variable au runtime — niveau 18 dans la précédence.
- **`cacheable: true`** sur `set_fact` persiste la valeur si `fact_caching` configuré.
- **`stat:` + `register:` + `when:`** = trio de la **logique conditionnelle** robuste.
- **`changed_when: false`** sur `command:` lecture-seule pour ne pas reporter `changed`.

## 🤔 Questions de réflexion

1. Vous lancez 5 commandes `dnf install` en `loop:`, et vous voulez **rapporter
   uniquement celles qui ont changé**. Comment formulez-vous le filtre sur le `register`
   ?

2. Pourquoi `set_fact:` est-il **niveau 18** (plus prioritaire que `vars:` du play à 14) ?
   Quel cas d'usage justifie cette précédence ?

3. Vous capturez la sortie d'un `command:` qui retourne un JSON multiligne. Comment
   parser ce JSON dans une variable Ansible utilisable ? (indice : `from_json` filtre).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`changed_when:`** + **`failed_when:`** : redéfinir l'état d'une tâche en fonction
  de la sortie. Voir lab 23.
- **`from_json`** / **`from_yaml`** : parser une sortie texte en structure native pour
  manipulation Jinja2.
- **`ansible_facts.<key>`** : namespace officiel pour les facts. Préférer
  `ansible_facts.distribution` à `ansible_distribution` dans les nouveaux playbooks
  (config `inject_facts_as_vars = false` à terme).
- **Pattern `register: r` + `r.stdout | trim`** : le `\n` final des commandes shell
  est un piège récurrent qui casse les comparaisons string.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/register-set-fact/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/register-set-fact/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/register-set-fact/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
