# Lab 14 — Facts et magic vars (`ansible_facts`, `hostvars`)

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

🔗 [**Facts et magic vars Ansible : ansible_facts, gather_subset, hostvars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/facts-magic-vars/)

Les **facts** sont des informations système collectées automatiquement par Ansible
au début d'un play (`gather_facts: true` par défaut) : OS, version, IP, mémoire,
CPU, interfaces réseau, etc. Les **magic vars** sont des variables fournies par
Ansible (pas par les managed nodes) : `inventory_hostname`, `groups`, `hostvars`,
`play_hosts`, `ansible_play_batch`, `ansible_play_hosts_all`. Maîtriser ces deux
catégories permet de **rendre vos playbooks dynamiques** et **multi-hôtes** sans
hardcoder de valeurs.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Lire** les facts système les plus utiles (`ansible_distribution`, `ansible_default_ipv4`).
2. **Utiliser** les magic vars (`inventory_hostname`, `groups`, `hostvars`).
3. **Accéder** aux facts d'un autre hôte via `hostvars['<hostname>']`.
4. **Limiter** la collecte avec `gather_subset:` pour gagner en performance.
5. **Désactiver** `gather_facts:` quand les facts ne sont pas nécessaires.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ping
```

## 📚 Exercice 1 — Voir tous les facts (curiosité)

Lancez `setup` en ad-hoc pour explorer :

```bash
ansible web1.lab -m ansible.builtin.setup | less
```

🔍 **Observation** : énorme output ! Chaque managed node renvoie **300-500 facts**.
Les plus utiles :

- `ansible_distribution`, `ansible_distribution_version` (`AlmaLinux`, `10.1`)
- `ansible_default_ipv4.address` (`10.10.20.21`)
- `ansible_memtotal_mb` (mémoire totale en MB)
- `ansible_processor_count` / `ansible_processor_vcpus` (CPU)
- `ansible_hostname` / `ansible_fqdn` (hostname court / FQDN)
- `ansible_kernel`, `ansible_architecture`
- `ansible_interfaces` (liste des interfaces réseau)

**Filtrer** un fact précis :

```bash
ansible web1.lab -m ansible.builtin.setup -a "filter=ansible_default_ipv4"
```

## 📚 Exercice 2 — Lire les facts dans un play

Créez `lab.yml` :

```yaml
---
- name: Demo facts systeme
  hosts: web1.lab
  become: true
  tasks:
    - name: Afficher les facts cles
      ansible.builtin.debug:
        msg: |
          host : {{ inventory_hostname }}
          fqdn : {{ ansible_fqdn }}
          os : {{ ansible_distribution }} {{ ansible_distribution_version }}
          kernel : {{ ansible_kernel }}
          memoire : {{ ansible_memtotal_mb }} MB
          cpu : {{ ansible_processor_vcpus }} vCPU
          ipv4 : {{ ansible_default_ipv4.address }}
          interfaces : {{ ansible_interfaces | join(', ') }}
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation** : tous les facts sont disponibles **sans `vars:`** — Ansible les a
collectés au début du play (`gather_facts: true` est implicite par défaut).

## 📚 Exercice 3 — Magic vars (`inventory_hostname`, `groups`, `hostvars`)

Modifiez `lab.yml` pour utiliser les magic vars :

```yaml
- name: Demo magic vars
  hosts: webservers
  tasks:
    - name: Afficher les magic vars
      ansible.builtin.debug:
        msg: |
          mon hostname (inventaire) : {{ inventory_hostname }}
          mon hostname (managed node) : {{ ansible_hostname }}
          membres du groupe webservers : {{ groups['webservers'] }}
          tous les hosts du play : {{ ansible_play_hosts_all }}
          batch courant : {{ ansible_play_batch }}
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation** :

- **`inventory_hostname`** = le nom **dans l'inventaire** (ce que Ansible voit). C'est
  toujours **`web1.lab`** ici, peu importe le hostname réel de la VM.
- **`ansible_hostname`** = le nom **rapporté par la VM** (`hostname -s`). Peut être
  différent (machine renommée, FQDN différent, etc.).
- **`groups['webservers']`** = liste des membres du groupe.
- **`ansible_play_hosts_all`** = tous les hôtes du play (même ceux qui ont échoué).
- **`ansible_play_batch`** = hôtes du **batch courant** (utile avec `serial:`).

## 📚 Exercice 4 — `hostvars` : accéder aux facts d'un autre hôte

```yaml
- name: Demo hostvars
  hosts: web1.lab
  become: true
  tasks:
    - name: Afficher des facts d autres hotes
      ansible.builtin.debug:
        msg: |
          IP de web2 : {{ hostvars['web2.lab'].ansible_default_ipv4.address | default('inconnu') }}
          OS de db1 : {{ hostvars['db1.lab'].ansible_distribution | default('inconnu') }}
```

**Lancez d'abord** :

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation** : selon que web2 et db1 ont déjà été "fact-gathered" dans cette
session, vous obtenez soit les vraies valeurs, soit `inconnu` (filtre `default`).

**Pourquoi** ? `hostvars` ne contient des facts que si Ansible **a contacté** ces
hôtes. Dans le play `hosts: web1.lab`, Ansible ne récolte que les facts de web1.

**Solution** : pré-collecter les facts en lançant un premier play `hosts: all`.

```yaml
---
- name: Pre-gather facts pour tout le lab
  hosts: all
  gather_facts: true
  tasks: []

- name: Vrai play qui utilise les facts d autres hotes
  hosts: web1.lab
  tasks:
    - name: Afficher l IP de web2 (maintenant disponible)
      ansible.builtin.debug:
        msg: "IP de web2 : {{ hostvars['web2.lab'].ansible_default_ipv4.address }}"
```

## 📚 Exercice 5 — `gather_subset:` pour limiter la collecte

Sur 100 hôtes, le `gather_facts: true` complet prend **30+ secondes**. Souvent, vous
n'avez besoin que d'une fraction.

```yaml
---
- name: Demo gather_subset minimaliste
  hosts: web1.lab
  gather_facts: true
  gather_subset:
    - "!all"        # Ne pas collecter tout
    - "!min"        # Meme pas le minimum
    - network       # Mais collecter network
  tasks:
    - name: Verifier ce qui est collecte
      ansible.builtin.debug:
        msg: |
          IP : {{ ansible_default_ipv4.address | default('non collecte') }}
          OS : {{ ansible_distribution | default('non collecte') }}
          memoire : {{ ansible_memtotal_mb | default('non collecte') }}
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation** :

- `ansible_default_ipv4.address` est disponible (subset `network` collecté).
- `ansible_distribution` et `ansible_memtotal_mb` peuvent être **absents** si non
  inclus.

**Subsets disponibles** : `all`, `min`, `network`, `hardware`, `virtual`, `facter`,
`ohai`. Le préfixe `!` exclut.

## 📚 Exercice 6 — Désactiver complètement `gather_facts`

Quand vous **n'avez besoin d'aucun fact** (juste copier un fichier, par exemple),
`gather_facts: false` économise 1-3s par hôte :

```yaml
---
- name: Play sans facts
  hosts: web1.lab
  gather_facts: false
  tasks:
    - name: Tester un fact (devrait planter)
      ansible.builtin.debug:
        msg: "OS : {{ ansible_distribution | default('non collecte') }}"

    - name: Mais inventory_hostname marche
      ansible.builtin.debug:
        msg: "host inventaire : {{ inventory_hostname }}"
```

🔍 **Observation** :

- `ansible_distribution` est `non collecte` (filtre default).
- `inventory_hostname` marche **toujours** — c'est une magic var Ansible, pas un fact.

## 🔍 Observations à noter

- **Facts** = collectés sur le managed node (`gather_facts: true`).
- **Magic vars** = fournies par Ansible (`inventory_hostname`, `groups`, `hostvars`).
- **`inventory_hostname`** ≠ **`ansible_hostname`** (nom inventaire vs nom réel VM).
- **`hostvars`** ne contient que les hôtes **déjà contactés** dans cette session.
- **`gather_subset:`** + **`gather_facts: false`** = leviers de **performance** sur grandes fleets.
- **Pré-collecter les facts** dans un play `hosts: all` avant un play multi-hôtes.

## 🤔 Questions de réflexion

1. Vous voulez générer un fichier `/etc/hosts` complet sur web1, contenant les IPs
   de **tous** les managed nodes. Quel pattern utilisez-vous (combinaison de `groups`,
   `hostvars`, `loop:`) ?

2. `ansible_fqdn` retourne `web1.lab` sur web1, mais `ansible_hostname` retourne juste
   `web1`. Quelle est la différence interne (qu'est-ce qui est interrogé sur le managed
   node) ?

3. Sur 200 hôtes, `gather_facts: true` met 1 minute. Vous n'avez besoin que des IPs
   et de l'OS. Que mettez-vous dans `gather_subset:` pour gagner du temps ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`fact_caching`** : configurer `ansible.cfg` avec `fact_caching = jsonfile` pour
  **persister les facts** entre runs. Évite la re-collecte sur les hôtes inchangés.
- **`ansible_local`** : facts custom déposés dans `/etc/ansible/facts.d/*.fact` côté
  managed node. Lus automatiquement et exposés sous `ansible_local.<filename>.<key>`.
- **`set_fact:`** + **`cacheable: true`** : créer un fact dynamique au runtime et
  le persister dans le cache. Voir lab 16.
- **Pattern `inventory_hostname_short`** : magic var qui donne juste `web1` au lieu
  de `web1.lab` — utile quand l'inventaire utilise des FQDN mais que vos templates
  veulent le nom court.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/facts-magic-vars/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/facts-magic-vars/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/facts-magic-vars/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
