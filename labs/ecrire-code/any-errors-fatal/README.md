# Lab 26 — `any_errors_fatal:` (arrêter le play sur 1ère erreur)

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

🔗 [**any_errors_fatal Ansible : arrêter le play sur 1ère erreur cluster**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/any-errors-fatal/)

Par défaut, Ansible **continue** le play sur les autres hôtes si **un** hôte échoue.
`any_errors_fatal: true` change ce comportement : **dès la première erreur**, le
play **s'arrête sur tous les hôtes**, même ceux qui n'ont pas encore commencé.

C'est l'inverse exact de `ignore_errors: true`. Cas d'usage : opérations
**transactionnelles cluster** qui doivent réussir partout ou nulle part — provisionner
un cluster Galera, configurer un quorum etcd, déployer un schéma de base de données.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Activer** `any_errors_fatal: true` au niveau du play.
2. **Comparer** avec le comportement par défaut sur 2+ hôtes.
3. **Distinguer** `any_errors_fatal: true` de `max_fail_percentage: 0`.
4. **Combiner** avec `serial:` pour des patterns "one fails → all stop".
5. **Choisir** entre `any_errors_fatal:` et `block/rescue` selon le scénario.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ping
ansible webservers -b -m shell -a "rm -f /tmp/aef-*.txt"
```

## 📚 Exercice 1 — Comportement par défaut (sans `any_errors_fatal`)

Créez `lab.yml` :

```yaml
---
- name: Demo defaut sans any_errors_fatal
  hosts: webservers
  become: true
  tasks:
    - name: Tache 1 - poser un marqueur
      ansible.builtin.copy:
        content: "tache 1 OK\n"
        dest: /tmp/aef-task1.txt
        mode: "0644"

    - name: Tache 2 - echec UNIQUEMENT sur web1
      ansible.builtin.command: /bin/false
      when: inventory_hostname == 'web1.lab'

    - name: Tache 3 - poser un autre marqueur
      ansible.builtin.copy:
        content: "tache 3 OK\n"
        dest: /tmp/aef-task3.txt
        mode: "0644"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/any-errors-fatal/lab.yml
```

🔍 **Observation** :

- web1 : tâche 1 OK → tâche 2 **plante** → web1 est **retiré** du play.
- web2 : tâche 1 OK → tâche 2 **skipped** (pas web1) → tâche 3 OK.

PLAY RECAP : `web1: failed=1`, `web2: ok=2`. **Web2 a continué** alors que web1
plantait.

```bash
ansible webservers -b -m command -a "ls /tmp/aef-task*.txt"
```

**Sur web1** : seulement `aef-task1.txt`. **Sur web2** : `aef-task1.txt` ET
`aef-task3.txt`.

## 📚 Exercice 2 — Avec `any_errors_fatal: true`

Modifiez le play :

```yaml
- name: Demo any_errors_fatal
  hosts: webservers
  become: true
  any_errors_fatal: true
  tasks:
    - ...  # meme tasks
```

**Reset, puis lancez** :

```bash
ansible webservers -b -m shell -a "rm -f /tmp/aef-*.txt"
ansible-playbook labs/ecrire-code/any-errors-fatal/lab.yml
```

🔍 **Observation** :

- web1 : tâche 1 OK → tâche 2 **plante**.
- web2 : tâche 1 OK → tâche 2 skipped → **tâche 3 NON exécutée** car le play
  s'arrête.

PLAY RECAP : **`failed=1` sur web1 ET sur web2** (même si web2 n'a pas planté).
**Le play entier est en échec**.

```bash
ansible webservers -b -m command -a "ls /tmp/aef-task*.txt"
```

**Web2** : seulement `aef-task1.txt`. La tâche 3 n'a pas tourné. C'est l'effet
`any_errors_fatal:`.

## 📚 Exercice 3 — Quand utiliser `any_errors_fatal: true`

Cas d'usage typiques où **on ne veut pas continuer** :

1. **Configurer un cluster** : si 1 nœud échoue à recevoir le certificat, **rien**
   ne doit être configuré sur les autres (ou on se retrouve avec un cluster cassé).
2. **Provisionner un quorum** (etcd, Consul) : si 1 nœud échoue, le quorum est
   compromis — autant tout arrêter et investiguer.
3. **Déploiement d'un schéma DB** : la migration sur le primaire échoue → les
   replicas ne doivent **surtout pas** appliquer la migration partielle.

```yaml
- name: Migration DB cluster (atomique)
  hosts: db_cluster
  any_errors_fatal: true
  tasks:
    - name: Backup avant migration
      ansible.builtin.command: pg_dump ...

    - name: Appliquer la migration
      ansible.builtin.command: psql -f /tmp/migration.sql
```

Si le backup échoue sur 1 nœud → **on ne tente pas** la migration sur les autres.

## 📚 Exercice 4 — `any_errors_fatal:` vs `max_fail_percentage:`

`max_fail_percentage:` est plus **fin** : il accepte un certain pourcentage d'échec
avant d'aborter.

```yaml
- name: Tolerance 20% d echec
  hosts: webservers
  serial: 5
  max_fail_percentage: 20
  tasks:
    - ...
```

| Directive | Effet |
|---|---|
| Aucune | Continue sur les hôtes qui marchent |
| `any_errors_fatal: true` | Stop dès **1** erreur |
| `max_fail_percentage: 0` | Identique à `any_errors_fatal: true` |
| `max_fail_percentage: 20` | Stop si **>20%** ont échoué dans le batch |
| `max_fail_percentage: 50` | Tolère jusqu'à 50% d'échec |

🔍 **Observation** : `any_errors_fatal: true` **équivalent à `max_fail_percentage: 0`**
pour un comportement strict. Préférer `max_fail_percentage:` pour avoir le contrôle
fin.

## 📚 Exercice 5 — Combinaison `any_errors_fatal:` + `block/rescue`

Question : si une tâche dans un `block/rescue` échoue mais le `rescue:` rattrape,
est-ce que `any_errors_fatal:` se déclenche ?

**Réponse** : **Non** — `any_errors_fatal:` ne se déclenche que sur des **erreurs
non rattrapées**.

```yaml
- name: Demo any_errors_fatal + block/rescue
  hosts: webservers
  any_errors_fatal: true
  tasks:
    - block:
        - name: Tache qui plante
          ansible.builtin.command: /bin/false
      rescue:
        - name: Rescue local
          ansible.builtin.debug:
            msg: "Rattrape"

    - name: Cette tache tourne quand meme
      ansible.builtin.debug:
        msg: "any_errors_fatal pas declenche"
```

🔍 **Observation** : le rescue **rattrape** la tâche `/bin/false`, donc
`any_errors_fatal:` **n'est pas déclenché** — le play continue. C'est le comportement
souhaitable : `any_errors_fatal:` ne se déclenche que sur des **erreurs non gérées**.

## 📚 Exercice 6 — Le piège : `any_errors_fatal:` + tâche `unreachable`

`unreachable` (host injoignable, SSH KO) est traité **différemment** selon les
versions d'Ansible.

Sur Ansible 2.x récents, `any_errors_fatal: true` **inclut** les `unreachable` :
si web1 devient injoignable pendant le play, `any_errors_fatal:` déclenche l'arrêt.

Sur les anciennes versions (avant 2.x), il fallait combiner avec
`max_fail_percentage:` pour gérer les `unreachable`.

🔍 **Observation** : tester avec `ansible --version` quelle est votre version. Sur
Ansible Core 2.20 (RHEL 10), `any_errors_fatal:` couvre bien les `unreachable`.

## 🔍 Observations à noter

- **Comportement par défaut** : Ansible continue sur les hôtes survivants en cas d'échec.
- **`any_errors_fatal: true`** au niveau play = **stop dès la 1ère erreur** sur tous les hôtes.
- **`max_fail_percentage: N`** = tolérance fine (`0` équivaut à `any_errors_fatal: true`).
- **Block/rescue rattrape avant `any_errors_fatal:`** — donc pas de stop si rescue OK.
- **Cas d'usage** : opérations cluster atomiques (DB cluster, quorum, certificats).
- **Anti-pattern** : `any_errors_fatal: true` sur un play d'audit (vous arrêtez tout
  pour 1 hôte qui n'avait pas le paquet — non sense).

## 🤔 Questions de réflexion

1. Vous déployez sur 100 webservers en `serial: 10`. Vous voulez aborter si **plus
   de 10%** d'un batch échoue. Quelle directive : `any_errors_fatal: true`,
   `max_fail_percentage: 10`, ou les deux ?

2. Pourquoi `any_errors_fatal: true` est-il **dangereux** sur un play d'**audit
   multi-hôtes** ?

3. Comment articuler `any_errors_fatal: true` + `block/rescue` pour avoir un
   comportement "abort sauf si on rattrape explicitement" ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`max_fail_percentage:` + `serial:`** = pattern **canary deploy avec
  circuit-breaker**. Voir lab 09.
- **Différence avec `force_handlers:`** : `any_errors_fatal:` arrête tout, mais
  les **handlers déjà notifiés** continuent par défaut. Avec `force_handlers: true`,
  on garantit que les handlers tournent même en cas d'abort.
- **`fail` module + `any_errors_fatal:`** : équivalent d'un `assert:` cluster — si
  une condition n'est pas satisfaite sur 1 hôte, on aborte le play.
- **Pattern `health-check play first`** : un premier play `any_errors_fatal: true`
  qui vérifie tous les prérequis, suivi du play de déploiement réel. Si le health-check
  fail, rien n'est déployé.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/any-errors-fatal/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/any-errors-fatal/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/any-errors-fatal/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
