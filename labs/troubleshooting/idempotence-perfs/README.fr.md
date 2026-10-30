# Lab 91 - Idempotence cassée et tuning des performances (forks, pipelining, ControlPersist)

> **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo.

## Rappel

Guide compagnon : [**Idempotence cassée et tuning des performances**](https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/)

Un playbook **idempotent** affiche `changed=0` au **second passage** : il a constaté que le système était déjà dans l'état voulu et n'a rien touché. Quand `changed=N` revient à chaque exécution, le récapitulatif ne permet plus de distinguer un vrai changement d'une tâche qui se rejoue pour rien, et un service peut être redémarré sans raison.

Ce lab vous fait diagnostiquer les trois causes les plus fréquentes (`shell` sans `creates:`, `lineinfile` sans `regexp:`, `command` de lecture sans `changed_when:`), les corriger, puis mesurer l'effet des réglages de connexion (`pipelining`, `forks`, `ControlPersist`) sur le temps total d'un playbook.

## Objectifs

À la fin de ce lab, vous saurez :

1. Identifier les modules qui ne sont pas idempotents par défaut (`command`, `shell`, `raw`, `script`).
2. Rendre un `shell` idempotent avec `creates:` ou `removes:`.
3. Fixer le verdict `changed` d'une tâche avec `changed_when:`, et distinguer ce mot-clé de `failed_when:`.
4. Relever une mesure de référence avec `profile_tasks` (voir le lab 89).
5. Régler `pipelining` et `forks` dans `ansible.cfg`, et savoir que `ControlPersist=60s` est déjà actif par défaut.
6. Comparer la mesure de référence et la version réglée sur un playbook multi-hôtes.

## Préparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible all -b -m ansible.builtin.file -a "path=/tmp/lab91-marker state=absent" 2>&1 | tail -2
```

## Arborescence cible

Vous écrivez vous-même `lab.yml` et `challenge/solution.yml`, et vous créez `ansible.cfg` à l'exercice 6.

```text
labs/troubleshooting/idempotence-perfs/
├── README.md
├── ansible.cfg                       ← (à créer en exo 6)
└── challenge/
    ├── README.md
    └── tests/
        └── test_functional.py
```

## Exercice 1 - `shell` sans `creates:`

Le module `shell` lance sa commande à chaque exécution, sans regarder l'état de la cible. Le playbook suivant crée un fichier marqueur :

```yaml
---
- hosts: db1.lab
  become: true
  tasks:
    - name: Créer un fichier marker (anti-pattern)
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
```

Lancez-le **deux fois** et lisez le récapitulatif :

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml | grep changed
```

Vous obtenez `changed=1` aux deux passages : le second ne devrait rien changer, la tâche n'est donc pas idempotente.

### Correction avec `creates:`

L'argument `creates:` indique à Ansible de sauter la commande si le fichier existe déjà :

```yaml
- name: Créer un fichier marker (idempotent)
  ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
  args:
    creates: /tmp/lab91-marker        # ← sauté si le fichier existe
```

Après correction, le premier passage affiche `changed=1` et le second `changed=0`.

## Exercice 2 - `lineinfile` sans `regexp:`

Sans `regexp:`, `lineinfile` cherche la ligne exacte donnée dans `line:`. Si la valeur change plus tard, il ne reconnaît plus l'ancienne ligne et en ajoute une seconde.

```yaml
- name: Modifier la config (anti-pattern)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    line: "max_connections = 100"
    state: present
    create: true
```

Jouez-la deux fois, puis changez la valeur en `max_connections = 200` : le fichier contient alors les deux lignes, `max_connections = 100` et `max_connections = 200`.

### Correction avec `regexp:`

Avec `regexp:`, le module repère la ligne existante et la remplace :

```yaml
- name: Modifier la config (idempotent)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    regexp: '^max_connections\s*='   # ← reconnaît la ligne existante
    line: "max_connections = 200"
    state: present
    create: true
```

Posez `regexp:` dès la première écriture de la directive : c'est ce qui permet de la modifier plus tard sans doublon.

## Exercice 3 - `command` de lecture sans `changed_when:`

Une commande de lecture ne modifie rien, mais `command` la déclare `changed` à chaque fois :

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  # sans changed_when, cette lecture seule est comptée comme un changement
```

### Correction avec `changed_when: false`

Pour une lecture, la réponse est `false` :

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  changed_when: false                 # ← lecture seule, jamais de changement
  register: curl_out
```

La tâche passe en `ok` à chaque exécution, et un vrai changement ailleurs dans le playbook reste visible dans le récapitulatif.

## Exercice 4 - `changed_when:` avec une expression, et `failed_when:`

Certaines commandes agissent sans prévenir Ansible, mais leur sortie indique si elles ont fait quelque chose. On lit alors cette sortie pour décider du verdict. `git init` écrit `Initialized empty Git repository` la première fois, et `Reinitialized existing Git repository` quand le dépôt existe déjà. En vrai on utiliserait le module `git` ou `file` ; la commande sert ici à montrer le mécanisme :

```yaml
- name: Initialiser le dépôt
  ansible.builtin.command: git init /tmp/depot
  register: init
  changed_when: "'Reinitialized' not in init.stdout"
```

Au premier passage la tâche est `changed`, au second elle est `ok`, alors que la commande a bien été relancée.

`changed_when:` ne dit rien de la réussite de la tâche. Pour décider qu'un résultat est un échec, c'est `failed_when:` qu'il faut. Un contrôle de santé qui répond mal ne doit pas apparaître comme « modifié » : il doit faire échouer la tâche, et comme il ne modifie rien, on le déclare avec `changed_when: false`.

```yaml
- name: Contrôler la santé de l'application
  ansible.builtin.uri:
    url: "http://localhost:8080/health"
    return_content: true
  register: health
  changed_when: false
  failed_when: "'OK' not in health.content"
```

Si le serveur répond 200 avec `KO` dans le corps, la tâche échoue et le récapitulatif affiche `failed=1`, sans `changed`. Avec `OK` dans le corps, elle passe en `ok`.

## Exercice 5 - Mesure de référence

Avant de régler quoi que ce soit, mesurez. Créez un playbook qui exécute cinq tâches sur plusieurs hôtes, avec la collecte des facts activée :

```yaml
---
- hosts: all
  gather_facts: true
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

Lancez-le avec la configuration par défaut et notez le temps :

```bash
time ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

Le temps dépend de votre environnement : c'est votre propre valeur qui sert de référence, relevez-la.

## Exercice 6 - Régler pipelining et forks

Créez un `ansible.cfg` au niveau du lab :

```ini
[defaults]
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200

[ssh_connection]
pipelining = True
```

Relancez la même mesure :

```bash
time ANSIBLE_CONFIG=labs/troubleshooting/idempotence-perfs/ansible.cfg \
  ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

Comparez avec votre mesure de l'exercice 5 : l'écart est le gain réel sur votre environnement.

Trois mécanismes entrent en jeu :

- `pipelining = True` évite de copier le module sur la cible avant de l'exécuter : l'exécution passe par une seule connexion SSH au lieu de plusieurs par tâche.
- `forks = 20` exécute jusqu'à 20 hôtes en parallèle (la valeur par défaut est 5).
- `ControlPersist` fait réutiliser une connexion SSH ouverte pour les tâches suivantes. Ce réglage est déjà actif : la valeur par défaut de `ssh_args` est `-C -o ControlMaster=auto -o ControlPersist=60s` (`ansible-doc -t connection ansible.builtin.ssh`), il n'y a donc rien à activer. Une ligne `ssh_args` dans `ansible.cfg` remplace cette valeur **en entier** : si vous la posez pour allonger la durée (`ControlPersist=300s`), reprenez aussi `-C` et `ControlMaster=auto`, sinon vous perdez la réutilisation de connexion au lieu de l'améliorer.

Le pipelining est incompatible avec `requiretty` dans `/etc/sudoers`. Sur les images RHEL personnalisées, vérifiez ce réglage.

## Exercice 7 - Tester l'idempotence en CI

Le test consiste à jouer le playbook deux fois sur une cible jetable et à exiger que le second passage ne change rien. Les deux passages doivent aussi réussir : un playbook qui échoue au second tour n'a rien d'idempotent, même si aucun `changed` n'apparaît.

Le piège d'un script naïf tient au `tee`. Dans un pipeline shell, le code de retour est celui de la dernière commande, donc celui de `tee`, qui réussit toujours. Sans `set -o pipefail`, un `ansible-playbook` qui échoue passe inaperçu, et chercher seulement `changed=[1-9]` dans le journal ne détecte rien si le play s'est arrêté avant d'avoir changé quoi que ce soit.

```bash
#!/usr/bin/env bash
set -euo pipefail

playbook="${1:?usage: $0 playbook.yml}"
log="$(mktemp)"
export ANSIBLE_NOCOLOR=1

# Premier passage : il peut modifier la cible, mais il doit réussir.
ansible-playbook "$playbook"

# Second passage : même réussite exigée, et aucun changement.
ansible-playbook "$playbook" | tee "$log"

if grep -Eq '(changed|failed|unreachable)=[1-9]' "$log"; then
  echo "Idempotence KO : le second passage a modifié ou échoué" >&2
  exit 1
fi
echo "Idempotence OK"
```

`set -e` arrête le script si le premier passage échoue. `pipefail` fait remonter le code de retour d'`ansible-playbook` à travers le `tee`, donc un second passage en échec arrête aussi le script. La recherche dans le récapitulatif (`PLAY RECAP`) couvre les trois compteurs qui doivent rester à zéro, et `ANSIBLE_NOCOLOR=1` évite que des séquences de couleur ne s'intercalent dans le journal.

Ce test n'est pas le mode `--check --diff`. Ce dernier simule une exécution sans rien modifier et montre ce qui changerait : il sert à détecter une dérive sur un système existant, ou à relire un changement avant de l'appliquer. Il ne remplace pas le test d'idempotence, parce que les tâches `command` et `shell` sont sautées en mode check (`skipping`), sauf avec `creates:` ou `removes:` : la condition est alors évaluée sans lancer la commande, et la tâche annonce `changed` si elle s'exécuterait, et que les tâches qui dépendent de leur résultat ne peuvent pas être évaluées. L'idempotence ne se vérifie qu'en appliquant réellement, d'où la cible jetable.

## À retenir

- `command`, `shell`, `raw` et `script` ne sont pas idempotents par défaut.
- `creates:` et `removes:` rendent un `shell` idempotent grâce à un test sur un fichier.
- `changed_when: false` s'applique aux commandes de lecture ; `failed_when:` décide de ce qui compte comme un échec.
- `lineinfile` s'écrit toujours avec `regexp:`.
- `ControlPersist=60s` est déjà le réglage par défaut ; `pipelining` et `forks` se jugent par une mesure avant et après.
- Un test d'idempotence exige que les deux passages réussissent et que le second ne rapporte ni `changed`, ni `failed`, ni `unreachable`.

## Questions de réflexion

1. Pourquoi `pipelining` est-il désactivé par défaut ?
2. Quand `changed_when: true` explicite (au lieu de `false`) est-il utile ?
3. Quels risques présente `forks=200` sur un poste standard ?
4. `creates:` accepte-t-il un glob comme `/tmp/lab91-*` ? (Indice : non, c'est un chemin exact.)

## Challenge final

Voir [`challenge/README.md`](challenge/README.md) : refactorer un playbook non idempotent vers un playbook idempotent avec `creates:`, `regexp:` et `changed_when:`.

## Pour aller plus loin

- Lab 92 : mock RHCE EX294.
- `ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks` active le chronométrage
  sans toucher à `ansible.cfg`. Un callback s'active par son nom dans cette liste ;
  il n'existe pas de variable `ANSIBLE_PROFILE_TASKS`, et la poser ne produit aucun effet.
- `stdout_callback = dense` affiche une ligne par hôte (utile sur de grands parcs).
- `fact_caching = redis` convient mieux que `jsonfile` sur un grand parc.

## Linter avec `ansible-lint`

```bash
ansible-lint labs/troubleshooting/idempotence-perfs/lab.yml
ansible-lint --profile production labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```
