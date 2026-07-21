# Lab 15 — Précédence des variables (22 niveaux RHCE EX294)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo (cf.
> [README racine](../../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Précédence des variables Ansible (les 22 niveaux officiels)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/)

Ansible définit **22 niveaux de précédence** pour les variables. Quand la même
variable est définie à plusieurs endroits, le **niveau le plus haut gagne**. Cette
mécanique est **explicitement testée à la RHCE EX294** — c'est un piège classique :
"j'ai bien défini `app_env: prod` dans `vars:` mais Ansible voit `dev` !". La réponse
est presque toujours dans la précédence.

L'ordre officiel (du plus faible au plus fort), tel que le donne la doc Ansible
[« Understanding variable precedence »](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence) :

```
role defaults (2)
< group_vars all (4 inventaire, 5 playbook)
< group_vars groupes (6 inventaire, 7 playbook)
< host_vars (9 inventaire, 10 playbook)
< facts / set_facts cachés (11)
< vars: du play (12)
< vars_prompt (13)
< vars_files: (14)
< role vars, roles/<role>/vars/main.yml (15)
< block vars (16)
< task vars (17)
< include_vars (18)
< set_fact / variables registered (19)
< role params (20)
< include params (21)
< -e --extra-vars (22 — gagne sur TOUT)
```

⚠️ **Le piège qui coûte le plus cher** : `vars_files:` (14) **bat** les `vars:`
du play (12). L'intuition dit le contraire (« ce que j'écris dans mon play est
plus proche, donc plus fort »), et c'est faux. Le fichier chargé gagne. C'est
**ça** qu'il faut mémoriser pour l'EX294, et c'est ce que vous allez mesurer à
l'exercice 3.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Démontrer** mécaniquement quel niveau gagne en superposant la même variable.
2. **Comprendre** pourquoi `--extra-vars` est l'arme finale.
3. **Distinguer** `vars:` du play (niveau 12) de `vars_files:` (niveau 14), et
   savoir **lequel gagne** quand les deux portent la même variable.
4. **Diagnostiquer** une variable qui "ne prend pas la valeur attendue".
5. **Choisir** le bon niveau pour chaque cas (default, override env, override CLI).

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING
mkdir -p labs/ecrire-code/precedence-variables/{group_vars,host_vars,vars}
ansible db1.lab -m ping
```

## 📚 Exercice 1 — Démonstration de base : 3 niveaux

Créez `group_vars/all.yml` :

```yaml
---
priority_test: "from_group_vars_all"
```

Créez `group_vars/dbservers.yml` :

```yaml
---
priority_test: "from_group_vars_dbservers"
```

Créez `lab.yml` :

```yaml
---
- name: Demo precedence
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: priority_test
```

**Avant de lancer**, **devinez** : qui gagne ?

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation** : `priority_test = from_play_vars`. Pourquoi ? Parce que
ces `group_vars/` sont posés à côté du playbook, donc :

- `group_vars/all.yml` (niveau 5) ← le plus faible des trois.
- `group_vars/dbservers.yml` (niveau 7) ← bat all (groupe plus spécifique).
- **`vars:` du play (niveau 12) ← bat les group_vars**.

## 📚 Exercice 2 — Ajouter `host_vars/`

Créez `host_vars/db1.lab.yml` :

```yaml
---
priority_test: "from_host_vars"
```

**Relancez** :

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation** : toujours `from_play_vars`. Pourquoi ? `host_vars/` (niveau 10
ici, posé à côté du playbook) est plus spécifique que `group_vars/`, mais
**toujours moins prioritaire que `vars:` du play (niveau 12)**.

**À retenir** : toute la **spécificité de l'inventaire** (host > group) reste
**sous** le play. Dès qu'une variable est écrite dans le play, l'inventaire ne
la reprend plus. Attention : ça ne veut pas dire que les `vars:` du play sont
imbattables, l'exercice 3 le montre.

## 📚 Exercice 3 — `vars_files:` (14) contre `vars:` du play (12)

C'est **le** duel du lab, et celui que l'intuition perd. Créez `vars/loader.yml` :

```yaml
---
priority_test: "from_vars_files"
```

Modifiez `lab.yml` pour charger ce fichier **en plus** des `vars:` du play :

```yaml
---
- name: Demo precedence vars_files
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  vars_files:
    - vars/loader.yml
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: priority_test
```

**Avant de lancer**, pariez. La plupart des gens parient `from_play_vars` : le
`vars:` est écrit dans le play, sous les yeux, alors que le fichier est « à
côté ». Lancez :

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation** : `priority_test = from_vars_files`. **`vars_files:`
(niveau 14) bat les `vars:` du play (niveau 12)**, et il n'y a pas d'exception :
l'ordre de déclaration dans le play n'y change rien, mettre `vars_files:` avant
ou après `vars:` non plus. Le niveau seul décide.

**Pourquoi ce sens ?** Les `vars:` du play sont conçus comme des **valeurs par
défaut du play** ; un `vars_files:` est une **décision d'exploitation**
(l'environnement, le site, le client). Il est donc normal que le fichier
l'emporte : c'est lui qui porte le choix, le play ne porte que le repli.

**À mémoriser pour l'EX294** : si vous posez une valeur dans `vars:` et qu'elle
« ne prend pas », cherchez un `vars_files:` avant d'accuser Ansible. Et si vous
voulez qu'une valeur du play soit **imbattable** par un fichier, ce n'est pas
`vars:` qu'il faut utiliser, mais un niveau supérieur (`set_fact`, exercice 4).

## 📚 Exercice 4 — Ajouter `set_fact` (niveau 19)

Modifiez `lab.yml` pour ajouter un `set_fact` :

```yaml
- name: Demo precedence avec set_fact
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  tasks:
    - name: Forcer la valeur via set_fact
      ansible.builtin.set_fact:
        priority_test: "from_set_fact"

    - name: Quelle valeur gagne maintenant ?
      ansible.builtin.debug:
        var: priority_test
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation** : `priority_test = from_set_fact`. **`set_fact` (niveau 19)**
bat **`vars:` du play (niveau 12)** et aussi **`vars_files:` (niveau 14)** de
l'exercice précédent. C'est utile quand vous voulez **calculer** une variable à
partir d'autres et que cette valeur **doit gagner** sur les défauts comme sur
les fichiers.

## 📚 Exercice 5 — `--extra-vars` (niveau 22 — l'arme finale)

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml \
  --extra-vars "priority_test=from_extra_vars"
```

🔍 **Observation** : `priority_test = from_extra_vars`. **`--extra-vars` (niveau 22)
bat même `set_fact` (niveau 19)**. Aucun mécanisme dans le playbook ne peut surcharger
`--extra-vars`.

**Cas d'usage typique** : un opérateur force une valeur lors d'un run d'urgence sans
modifier le code, ou la CI/CD passe `--extra-vars` calculés à partir de l'environnement.

## 📚 Exercice 6 — Le piège des dicts : merge vs override

Avec un **dict**, la précédence ne fait pas un merge intelligent — elle **remplace
complètement**. Démonstration :

Créez `group_vars/dbservers-dict.yml` :

```yaml
---
db_config:
  host: db1.lab
  port: 5432
  pool_size: 10
```

Modifiez `lab.yml` :

```yaml
- name: Demo precedence dicts
  hosts: db1.lab
  vars:
    db_config:
      host: db1.lab
      port: 5432
      timeout: 30
  tasks:
    - name: Afficher le dict resultant
      ansible.builtin.debug:
        var: db_config
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation** : `db_config` a **3 clés** : `host`, `port`, `timeout`. **PAS de
`pool_size`**. Pourquoi ? Parce que `vars:` du play **a remplacé complètement** le
dict des group_vars — pas de merge.

**Solution** : utiliser le filtre **`combine`** ou activer
`hash_behaviour = merge` dans `ansible.cfg` (déconseillé car implicite et global).

```yaml
vars:
  db_config: "{{ db_config_base | combine({'timeout': 30}, recursive=True) }}"
```

## 📚 Exercice 7 — Diagnostic : pourquoi ma variable est-elle bizarre ?

Outil n°1 : afficher **toutes les vars** vues par Ansible :

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml -vvv 2>&1 | grep -A2 "priority_test"
```

🔍 **Observation** : avec `-vvv`, Ansible affiche les vars chargées et leur source.
Cherchez la **dernière** mention de `priority_test` — c'est la valeur effective.

Outil n°2 : poser un `debug:` au début et à la fin du play pour comparer :

```yaml
- name: Diagnostic debut play
  ansible.builtin.debug:
    var: priority_test

# ... vos taches ...

- name: Diagnostic fin play
  ansible.builtin.debug:
    var: priority_test
```

Si la valeur change entre les deux, c'est qu'un `set_fact` ou `register: + with_*`
intermédiaire a tapé dessus.

## 🔍 Observations à noter

- **`--extra-vars` (22)** > `role params` (20) > `set_fact` (19) > `include_vars` (18) > `role vars` (15) > **`vars_files:` (14)** > **`vars:` du play (12)** > `facts` (11) > `host_vars` (9-10) > `group_vars/<grp>` (6-7) > `group_vars/all` (4-5) > `role defaults` (2).
- **`vars_files:` (14) BAT `vars:` du play (12)**. C'est le point contre-intuitif du lab : le fichier chargé gagne sur ce qui est écrit dans le play.
- **Spécificité d'inventaire** (host > group) **ne bat pas** le play : tout l'inventaire reste sous le niveau 12.
- **Dicts** ne sont **pas merged** par défaut — un niveau supérieur **remplace** complètement.
- **`combine(recursive=True)`** est l'outil pour un vrai merge de dicts.
- **`-vvv`** + grep permet de tracer la source d'une valeur.

## 🤔 Questions de réflexion

1. Vous voulez qu'un opérateur puisse forcer `app_env=prod` lors d'un déploiement
   d'urgence sans toucher au code. Quel niveau utilisez-vous, et pourquoi pas
   `host_vars/` (niveau 9-10) qui semble "plus officiel" ?

2. Vous avez un dict `database:` défini dans `group_vars/all.yml` avec 5 clés. Vous
   voulez **ajouter** une 6e clé pour le groupe `dbservers` sans réécrire les 5
   premières. Comment ?

3. Pourquoi `set_fact` (niveau 19) est-il **plus prioritaire** que `vars:` du play
   (niveau 12) ? Quel est le **cas d'usage** qui justifie cette précédence ?

4. Un collègue affirme : « les `vars:` de mon play sont ce qu'il y a de plus fort,
   à part `--extra-vars` ». Donnez-lui **deux** contre-exemples pris dans ce lab,
   dont un qui ne demande **aucune** tâche à exécuter.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`include_vars:` dynamique** (niveau 18) : charger un fichier de vars selon une
  condition runtime, niveau supérieur à `vars_files:` (statique, niveau 14).
  Attention : `set_fact` (19) reste **au-dessus** d'`include_vars` (18), même si
  l'`include_vars` s'exécute **après** dans le play. Le niveau prime sur l'ordre
  chronologique.
- **Role defaults vs role vars** : `roles/<role>/defaults/main.yml` (niveau 2, le
  plus faible, facile à override) vs `roles/<role>/vars/main.yml` (niveau 15,
  au-dessus de `vars_files:`, difficile à override). À choisir selon l'intention.
- **`ANSIBLE_HASH_BEHAVIOUR=merge`** : variable d'env qui change globalement le
  comportement des dicts. **Déconseillé** — préférer `combine` explicite par variable.
- **Pattern `var | default(<lookup_chaine>)`** : fallback en chaîne pour reproduire
  une logique de précédence custom.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/precedence-variables/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/precedence-variables/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/precedence-variables/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
