# Lab 91 — Idempotence cassée et tuning performances (forks, pipelining, ControlPersist)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Idempotence cassée et tuning des performances**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/)

Un playbook **idempotent** affiche `changed=0` au **second passage**. Si vous voyez `changed=N` à chaque run, **vos tâches mentent** sur leur état — chaque exécution refait tout, casse les caches HTTP/CDN, redémarre des services inutilement, et fait perdre confiance dans le code.

Ce lab vous apprend à **diagnostiquer** les 3 anti-patterns les plus fréquents (`shell` sans `creates:`, `lineinfile` sans `regexp:`, `command` sans `changed_when:`), à les **fixer**, et à **mesurer** l'impact d'optimisations SSH (`pipelining`, `forks`, `ControlPersist`) sur le temps total d'un playbook.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Identifier** les modules non-idempotents par défaut (`command`, `shell`, `raw`, `script`).
2. **Rendre idempotent** un `shell` avec **`creates:`** ou **`removes:`**.
3. **Forcer le verdict `changed`** d'une tâche avec **`changed_when:`**.
4. **Mesurer** un baseline de temps avec `profile_tasks` (cf lab 89).
5. **Activer pipelining + forks=20 + ControlPersist=60s** dans `ansible.cfg`.
6. **Comparer** baseline vs optimisé sur un playbook multi-host.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible all -b -m ansible.builtin.file -a "path=/tmp/lab91-marker state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/troubleshooting/idempotence-perfs/
├── README.md
├── Makefile
├── ansible.cfg                       ← (à créer en exo 5)
└── challenge/
    ├── README.md
    └── tests/
        └── test_idempotence.py
```

L'apprenant écrit lui-même `lab.yml` et `challenge/solution.yml`.

## 📚 Exercice 1 — Anti-pattern `shell` sans `creates:`

```yaml
---
- hosts: db1.lab
  become: true
  tasks:
    - name: Créer un fichier marker (anti-pattern)
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
```

Lancer **2 fois** :

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml | grep changed
```

Sortie :

```text
changed=1   ← run 1
changed=1   ← run 2 (PROBLÈME : non idempotent)
```

🔍 **Observation** : `shell` exécute **toujours** la commande sans vérifier l'état. **Toujours** `changed=1`.

### Fix avec `creates:`

```yaml
- name: Créer un fichier marker (idempotent)
  ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
  args:
    creates: /tmp/lab91-marker        # ← skip si le fichier existe
```

Sortie après fix :

```text
changed=1   ← run 1
changed=0   ← run 2 (correct)
```

## 📚 Exercice 2 — Anti-pattern `lineinfile` sans `regexp:`

```yaml
- name: Modifier la config (anti-pattern)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    line: "max_connections = 100"
    state: present
    create: true
```

Lancer **2 fois**. Si la valeur change un jour :

```yaml
- name: Modifier la config (anti-pattern, MAJ)
  ansible.builtin.lineinfile:
    line: "max_connections = 200"
```

Le fichier contient maintenant **les 2 lignes** : `max_connections = 100` ET `max_connections = 200`. **Duplication**.

### Fix avec `regexp:`

```yaml
- name: Modifier la config (idempotent)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    regexp: '^max_connections\s*='   # ← match les lignes existantes
    line: "max_connections = 200"
    state: present
    create: true
```

🔍 **Observation** : avec `regexp:`, lineinfile **remplace** la ligne au lieu d'en ajouter une. Toujours **mettre `regexp:`** sauf si on est sûr de la première mise en place.

## 📚 Exercice 3 — Anti-pattern `command` sans `changed_when:`

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  # ↑ retourne toujours changed=1 alors qu'on lit seulement
```

### Fix avec `changed_when: false`

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  changed_when: false                 # ← lecture seule, jamais de changement
  register: curl_out
```

🔍 **Observation** : `changed_when: false` est le pattern pour les **commandes de lecture/diagnostic**. Préserve l'idempotence du playbook.

## 📚 Exercice 4 — `changed_when:` conditionnel

Un cas plus subtil : on veut signaler `changed` **uniquement** si la sortie contient une erreur.

```yaml
- name: Health check API
  ansible.builtin.uri:
    url: "http://localhost:8080/health"
    return_content: true
  register: health
  changed_when: "'OK' not in health.content"
```

🔍 **Observation** : `changed_when:` accepte une expression Jinja2/Python. Permet de **dériver** l'état changed du résultat de la tâche, pas du module.

## 📚 Exercice 5 — Baseline performances

Créer un playbook qui exécute **5 tâches** sur **3 hosts** :

```yaml
---
- hosts: all
  gather_facts: true                 # ← intentionnellement coûteux
  tasks:
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
```

Lancer **sans optimisation** (config par défaut) :

```bash
time ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

Mesurer le temps. Sur 3 hosts × 5 tâches × 0.5s + overhead SSH = ~15-20 s typique.

## 📚 Exercice 6 — Activer pipelining + forks + ControlPersist

Créer `ansible.cfg` au niveau du lab :

```ini
[defaults]
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200

[ssh_connection]
pipelining = True
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
```

Re-lancer :

```bash
time ANSIBLE_CONFIG=labs/troubleshooting/idempotence-perfs/ansible.cfg \
  ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

**Cible : -50 % à -60 %** sur le temps total.

🔍 **Observation** : 3 leviers cumulés :

- **`pipelining=True`** : supprime `mkdir tmp + scp + exec` → 1 SSH au lieu de 3 par tâche.
- **`forks=20`** : exécute 20 hosts en parallèle (default 5).
- **`ControlPersist=60s`** : connexion SSH **réutilisée** pendant 60s. Évite 1 handshake par tâche.

⚠️ **Pipelining incompatible avec `requiretty`** dans `/etc/sudoers`. Sur les images custom RHEL, vérifier.

## 📚 Exercice 7 — Tester l'idempotence en CI

Pour automatiser la vérification d'idempotence dans la CI :

```bash
# Run 1
ansible-playbook lab.yml > /tmp/run1.log
# Run 2
ansible-playbook lab.yml | tee /tmp/run2.log

# Échec si le 2e run a des changes
grep -E 'changed=[1-9]' /tmp/run2.log && echo "IDEMPOTENCE KO" && exit 1
echo "IDEMPOTENCE OK"
```

🔍 **Observation** : un test idempotence en CI **bloque** les régressions où un dev oublie un `changed_when:` ou un `creates:`. **À mettre dans le pipeline `ansible-playbook --check --diff`**.

## 🔍 Observations à noter

- **`command`, `shell`, `raw`, `script`** = non-idempotents par défaut.
- **`creates:`** / **`removes:`** rendent un `shell` idempotent en check de fichier.
- **`changed_when: false`** pour les commandes de lecture/diagnostic.
- **`lineinfile`** **toujours** avec `regexp:`.
- **3 leviers SSH** : `pipelining`, `forks`, `ControlPersist`.
- **Test idempotence** = run 2× et vérifier `changed=0`.

## 🤔 Questions de réflexion

1. Pourquoi `pipelining` est-il désactivé par défaut ?
2. Quand **`changed_when: true`** explicite (au lieu de `false`) est-il utile ?
3. **`forks=200`** sur un poste standard : risques ?
4. **`creates:` accepte-t-il un glob** comme `/tmp/lab91-*` ? (Indice : non, exact path).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — refactorer un playbook **non idempotent** vers un playbook **idempotent** avec `creates:` + `regexp:` + `changed_when:`.

## 💡 Pour aller plus loin

- **Lab 92** : Mock RHCE EX294.
- **`ANSIBLE_PROFILE_TASKS=1`** sans toucher à `ansible.cfg`.
- **`stdout_callback = dense`** : 1 ligne par host (utile flottes 50+ hosts).
- **`fact_caching = redis`** pour fleet > 100 hosts (jsonfile devient lent).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/troubleshooting/idempotence-perfs/lab.yml
ansible-lint --profile production labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```
