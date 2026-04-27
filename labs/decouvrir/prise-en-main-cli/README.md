# Lab 03 — Prise en main de la CLI (les 8 commandes du quotidien)

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

🔗 [**Prise en main de la CLI Ansible : les 8 commandes du quotidien**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/prise-en-main-cli/)

Ansible se manipule via **8 commandes** qui ont chacune un rôle précis. La plupart des labs n'en utilisent que 2 (`ansible` et `ansible-playbook`), mais en production vous toucherez régulièrement les 6 autres pour diagnostiquer, sécuriser ou linter votre code.

| Commande | À quoi ça sert | Quand l'utiliser |
| --- | --- | --- |
| **`ansible`** | Exécuter **un seul module** sur un pattern d'hôtes (mode ad-hoc) | Tester, dépanner, lancer une opération ponctuelle |
| **`ansible-playbook`** | Exécuter un **playbook YAML** | 90 % du temps |
| **`ansible-doc`** | Documentation **hors-ligne** des modules | Avant d'utiliser un module inconnu |
| **`ansible-config`** | Voir la **configuration active** | Quand un comportement vous surprend |
| **`ansible-inventory`** | Valider l'**inventaire** (groupes, vars résolues) | Avant un déploiement, en debug |
| **`ansible-galaxy`** | Installer **collections** et **rôles** | Mise en place d'un projet, mise à jour |
| **`ansible-vault`** | **Chiffrer** des fichiers sensibles | Mots de passe, clés API, certificats |
| **`ansible-lint`** | Détecter les **anti-patterns** | Avant un commit, dans la CI |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Exécuter une commande **ad-hoc** sur tous les managed nodes.
2. Trouver la doc d'un module **sans Internet** via `ansible-doc`.
3. Inspecter la **configuration active** et l'**inventaire** résolus.
4. Lister et installer des **collections** via `ansible-galaxy`.
5. **Chiffrer / déchiffrer** un fichier de variables avec `ansible-vault`.
6. **Linter** un playbook avec `ansible-lint`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
```

Réponse attendue : 4 `pong` (un par managed node). Si KO, lancez `make provision` à la racine.

## 📚 Exercice 1 — `ansible` : commande ad-hoc

Le mode **ad-hoc** exécute un seul module sur un pattern d'hôtes, sans playbook. Idéal pour tester une connexion ou collecter une info ponctuelle.

```bash
ansible all -m ansible.builtin.ping
```

🔍 **Observation** : 4 `pong` doivent revenir. Le module `ping` n'est **pas** un ICMP — il ouvre une connexion SSH puis lance un mini-script Python sur le managed node. C'est donc un **test bout-en-bout** de toute la chaîne Ansible (SSH + Python distant).

Variantes utiles :

```bash
ansible webservers -m ansible.builtin.command -a "uptime"           # uptime sur les webs
ansible db1.lab -b -m ansible.builtin.dnf -a "name=httpd state=absent"   # désinstaller httpd
ansible all -m ansible.builtin.setup -a "filter=ansible_distribution"    # collecter un fact
```

## 📚 Exercice 2 — `ansible-playbook` : exécuter un playbook

```bash
ansible-playbook labs/bootstrap/prepare-managed-nodes/playbook.yml
```

🔍 **Observation** : le playbook de préparation se déroule. Au **premier run**, des tâches sont marquées `changed`. Au **second run**, le `PLAY RECAP` affiche `changed=0` partout — c'est l'idempotence du lab 01 en action.

> 💡 Toutes les commandes `ansible-playbook` du repo se lancent **depuis la racine** — c'est pour ça que l'inventaire utilise un chemin relatif `{{ inventory_dir }}/../ssh/id_ed25519`.

## 📚 Exercice 3 — `ansible-doc` : documentation hors-ligne

`ansible-doc` est votre **manuel local** — pas besoin d'Internet pour comprendre un module.

```bash
ansible-doc ansible.builtin.dnf | less
```

🔍 **Observation** : la doc d'un module a 4 sections clés :

- **Description** (en haut) : à quoi sert le module.
- **Options** : tous les paramètres avec leur **type**, **défaut**, et indication `required`.
- **Examples** : snippets YAML prêts à copier.
- **Returns** : les attributs disponibles dans `register:` (utile dès le lab 17).

Pour lister tous les modules d'une collection :

```bash
ansible-doc -l ansible.builtin | head -20      # modules ansible.builtin uniquement
ansible-doc -l | grep -i firewall              # filtrer par mot-clé
```

## 📚 Exercice 4 — `ansible-config` : configuration active

Quand Ansible se comporte de façon inattendue (un timeout long, des facts manquants, des warnings sur le SSH), c'est presque toujours **un paramètre de config** qui surcharge le défaut.

```bash
ansible-config dump --only-changed
```

🔍 **Observation** : la sortie liste **uniquement** les paramètres qui diffèrent du défaut, avec leur **source** :

```text
DEFAULT_HOST_LIST(/.../ansible-training/ansible.cfg) = ['/.../inventory/hosts.yml']
HOST_KEY_CHECKING(/.../ansible-training/ansible.cfg) = False
INTERPRETER_PYTHON(/.../ansible-training/ansible.cfg) = auto_silent
```

Chaque ligne dit **quel paramètre est modifié** + **par quel fichier**. Si un comportement vous surprend, lancez d'abord cette commande.

## 📚 Exercice 5 — `ansible-inventory` : valider l'inventaire

```bash
ansible-inventory --graph
```

🔍 **Observation** : vue arborescente des groupes :

```text
@all:
  |--@control:
  |  |--control-node.lab
  |--@webservers:
  |  |--web1.lab
  |  |--web2.lab
  |--@dbservers:
  |  |--db1.lab
  |--@rhce_lab:
  |  |--@webservers:
  ...
```

Pour voir **toutes les variables résolues** d'un hôte (utile en debug d'héritage `group_vars`) :

```bash
ansible-inventory --host web1.lab
```

## 📚 Exercice 6 — `ansible-galaxy` : gérer les collections

Lister ce qui est déjà installé :

```bash
ansible-galaxy collection list
```

🔍 **Observation** : vous devez voir au moins `ansible.posix`, `community.general`, `community.libvirt` (cf. lab 02). Pour installer une nouvelle collection :

```bash
ansible-galaxy collection install community.docker
```

Pour réinstaller toutes les collections du repo en une commande :

```bash
ansible-galaxy collection install -r requirements.yml
```

## 📚 Exercice 7 — `ansible-vault` : chiffrer un secret

Vous ne stockerez **jamais** un mot de passe en clair dans un repo Git. `ansible-vault` chiffre un fichier (ou une variable seule) avec AES-256.

```bash
echo "api_key: secret-ABC123" > /tmp/secrets.yml
ansible-vault encrypt /tmp/secrets.yml         # demande un mot de passe (saisissez "test")
cat /tmp/secrets.yml                            # → contenu chiffré ($ANSIBLE_VAULT;1.1;AES256...)
ansible-vault view /tmp/secrets.yml             # → affiche en clair (mot de passe demandé)
ansible-vault decrypt /tmp/secrets.yml          # → remet en clair sur disque
rm /tmp/secrets.yml
```

🔍 **Observation** :

- Un fichier chiffré commence **toujours** par `$ANSIBLE_VAULT;1.1;AES256` (le `1.1` est la version du format).
- `view` ne touche pas au disque (lecture seule). `decrypt` réécrit le fichier en clair.
- Le mot de passe peut être passé via **`--vault-password-file`** (pour la CI/CD) au lieu d'être saisi à la main. C'est ce que fait le challenge.

## 📚 Exercice 8 — `ansible-lint` : qualité du code

`ansible-lint` détecte les **anti-patterns** dans un playbook : tâche sans `name:`, FQCN manquant, modules dépréciés, `shell:` sans `creates:`, etc.

```bash
ansible-lint labs/bootstrap/prepare-managed-nodes/playbook.yml
```

🔍 **Observation** : si le playbook est conforme, **sortie vide** (et exit 0). Sinon, chaque infraction est listée avec le numéro de ligne et la règle violée.

Profile **production** (le plus strict) :

```bash
ansible-lint --profile production labs/bootstrap/prepare-managed-nodes/
```

## 📚 Exercice 9 — Tout enchaîner via Make

Le `Makefile` du lab joue 6 commandes en chaîne pour vous donner une vue d'ensemble :

```bash
make -C labs/decouvrir/prise-en-main-cli run
```

🔍 **Observation** : enchaînement `ansible ping → ansible-doc -l → ansible-config dump → ansible-inventory --graph → ansible-galaxy list → ansible-lint`. Si **toutes** les sorties sont propres, votre poste est prêt pour les labs suivants.

## 🔍 Observations à noter

- **`ansible`** (sans suffixe) = ad-hoc. **`ansible-playbook`** = playbook. Ne pas confondre.
- Le **FQCN** (`ansible.builtin.dnf` au lieu de `dnf`) est **obligatoire** pour la RHCE 2026 et fortement recommandé partout — il garantit qu'Ansible appelle le bon module quand plusieurs collections en exposent un de même nom.
- `ansible-doc` lit la doc **embarquée** dans le module Python — donc disponible hors-ligne et toujours à jour avec votre version installée.
- `ansible-vault` chiffre **un fichier entier**. Pour chiffrer **une seule variable** dans un fichier YAML clair, utilisez `ansible-vault encrypt_string` (vu plus tard, section Vault).
- `ansible-lint --profile production` est le mode strict. Existent aussi `min`, `basic`, `moderate`, `safety`, `shared` du moins au plus strict.

## 🤔 Questions de réflexion

1. Vous voulez vérifier **rapidement** que les 4 managed nodes sont joignables et que le sudo fonctionne. Quelle commande utiliser ? Avec `ansible -b` ? `-m ping` ? `-m command -a "id"` ?

2. Un collègue vous dit : « Mon playbook met 30 secondes à démarrer alors qu'avant c'était instantané ». Quelle commande lancer en premier pour diagnostiquer ?

3. Vous voulez chiffrer **un seul mot de passe** dans un fichier `vars.yml` qui contient déjà 10 autres variables non sensibles. `ansible-vault encrypt` est-il le bon outil ? Si non, lequel ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire un script `solution.sh` qui automatise un cycle complet `ansible-vault` (chiffrer → vérifier le header → déchiffrer) avec un fichier de mot de passe (`--vault-password-file`). C'est le pattern utilisé en CI quand le mot de passe est fourni par un secret manager.

```bash
pytest -v labs/decouvrir/prise-en-main-cli/challenge/tests/
```

## 💡 Pour aller plus loin

- **`ansible-navigator`** : un wrapper TUI qui exécute les playbooks dans un Execution Environment (image OCI) — recommandé pour la RHCE 2026. Lancez `ansible-navigator run labs/bootstrap/prepare-managed-nodes/playbook.yml --mode stdout` pour voir la différence.
- **`ansible-builder`** : construit des Execution Environments custom à partir d'un fichier YAML. C'est ainsi qu'on garantit qu'un playbook tourne **identiquement** sur le poste dev, en CI et en prod.
- **Hooks Git pré-commit** : intégrez `ansible-lint --profile production` dans un hook pre-commit pour bloquer les commits qui introduiraient des anti-patterns.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/decouvrir/prise-en-main-cli/lab.yml

# Lint de votre solution challenge
ansible-lint labs/decouvrir/prise-en-main-cli/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/decouvrir/prise-en-main-cli/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
