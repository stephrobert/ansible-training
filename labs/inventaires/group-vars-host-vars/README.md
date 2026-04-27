# Lab 55 — group_vars et host_vars structurés

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Inventaires Ansible : group_vars et host_vars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/group-vars-host-vars/)

Ansible cherche **automatiquement** des variables dans deux dossiers placés **à côté de l'inventaire** :

- **`group_vars/<nom_groupe>.yml`** : variables appliquées à **tous les hôtes du groupe**.
- **`host_vars/<nom_hote>.yml`** : variables appliquées à **un seul hôte** (priorité plus haute).

Il existe aussi le groupe spécial **`all`** : `group_vars/all.yml` est appliqué à **tous les hôtes** de l'inventaire.

**Précédence (de la plus faible à la plus forte)** :

```text
1. group_vars/all.yml
2. group_vars/<groupe parent>.yml
3. group_vars/<groupe enfant>.yml
4. host_vars/<host>.yml
```

C'est cette **précédence** que vous allez démontrer dans ce lab.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Structurer un **inventaire YAML** avec `group_vars/` et `host_vars/` à côté.
2. Définir une variable à **3 niveaux** différents (all → groupe → host).
3. Vérifier la **valeur résolue** par `ansible-inventory --host <host>`.
4. Démontrer que la **règle "le plus local gagne"** s'applique.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/inventaires/group-vars-host-vars
```

## ⚙️ Arborescence cible

```text
labs/inventaires/group-vars-host-vars/
├── README.md           ← ce fichier
├── inventory/
│   ├── hosts.yml       ← inventaire YAML
│   ├── group_vars/
│   │   ├── all.yml
│   │   └── webservers.yml
│   └── host_vars/
│       └── web1.lab.yml
└── challenge/
    ├── README.md
    ├── solution.yml
    └── tests/
        └── test_precedence.py
```

## 📚 Exercice 1 — L'inventaire YAML

Créez `inventory/hosts.yml` :

```yaml
---
all:
  children:
    webservers:
      hosts:
        web1.lab:
        web2.lab:
    dbservers:
      hosts:
        db1.lab:
```

🔍 **Observation** : la structure `all.children.<groupe>.hosts.<host>` est la **forme YAML standard**. Pas besoin de spécifier `ansible_host:` si la résolution DNS ou `/etc/hosts` est correcte.

## 📚 Exercice 2 — Variable au niveau `all` (faible précédence)

Créez `inventory/group_vars/all.yml` :

```yaml
---
app_port: 80
```

Cette valeur s'applique à **tous les hôtes** par défaut.

## 📚 Exercice 3 — Variable au niveau d'un groupe

Créez `inventory/group_vars/webservers.yml` :

```yaml
---
app_port: 8080
```

🔍 **Observation** : `app_port` est maintenant **redéfini** pour les hôtes du groupe `webservers`. La précédence dit que `group_vars/webservers.yml` **gagne** sur `group_vars/all.yml`.

## 📚 Exercice 4 — Variable au niveau d'un host

Créez `inventory/host_vars/web1.lab.yml` :

```yaml
---
app_port: 9090
```

🔍 **Observation** : pour `web1.lab` spécifiquement, `app_port` vaut **9090** — la valeur la plus locale gagne.

## 📚 Exercice 5 — Vérifier la résolution

```bash
ansible-inventory -i inventory/hosts.yml --host web1.lab
ansible-inventory -i inventory/hosts.yml --host web2.lab
ansible-inventory -i inventory/hosts.yml --host db1.lab
```

**Sorties attendues** :

| Host | `app_port` résolu | Source |
|---|---|---|
| `web1.lab` | **9090** | `host_vars/web1.lab.yml` |
| `web2.lab` | **8080** | `group_vars/webservers.yml` |
| `db1.lab` | **80** | `group_vars/all.yml` |

🔍 **Observation** : Ansible fusionne automatiquement les variables des **3 niveaux** et garde la **plus locale**. C'est exactement ce qu'on attend pour configurer un parc avec quelques exceptions ponctuelles.

## 📚 Exercice 6 — Vérifier le graph

```bash
ansible-inventory -i inventory/hosts.yml --graph
```

**Sortie attendue** :

```text
@all:
  |--@dbservers:
  |  |--db1.lab
  |--@ungrouped:
  |--@webservers:
  |  |--web1.lab
  |  |--web2.lab
```

🔍 **Observation** : `@ungrouped` apparaît même vide — c'est normal, c'est un groupe spécial qui contient les hôtes hors groupe.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible all (4 VMs) ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Si vous ajoutez `app_port: 1234` dans le **playbook** (`vars: app_port: 1234`), quelle valeur gagne sur `web1.lab` ?

2. Comment **forcer** une valeur partout, qui ne peut être surchargée par aucun group_vars/host_vars ? (Indice : `--extra-vars`.)

3. Vous voulez stocker **un secret** chiffré pour `db1.lab`. Où le placez-vous et avec quel outil ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande de définir 3 variables à différents niveaux et de prouver leur résolution via un playbook qui crée des fichiers marqueurs sur chaque host. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **`group_vars/<groupe>/main.yml`** : si une seule variable devient un dossier, vous pouvez splitter (`main.yml`, `vault.yml`, `network.yml`).
- **Précédence complète (22 niveaux)** : voir la [page dédiée](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/).
- **Patterns d'hôtes** : voir [lab 56 — patterns d'hôtes](../56-inventaires-patterns-hotes/) pour cibler avec `--limit`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/inventaires/group-vars-host-vars/lab.yml
ansible-lint labs/inventaires/group-vars-host-vars/challenge/solution.yml
ansible-lint --profile production labs/inventaires/group-vars-host-vars/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
