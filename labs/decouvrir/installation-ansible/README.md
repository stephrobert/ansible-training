# Lab 02 — Installation d'Ansible (vérifier votre poste de contrôle)

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

🔗 [**Installer Ansible : pipx, mise, dnf, Execution Environment**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/)

Avant d'écrire le moindre playbook, il faut **un poste de contrôle qui marche** : Ansible installé, les bons binaires dans le `PATH`, les collections principales présentes. Ce lab ne demande **rien à écrire** — vous allez **inspecter** votre installation et apprendre à diagnostiquer un poste mal configuré.

La page du blog présente les **5 méthodes d'installation** recommandées en 2026 :

| Méthode | Pour qui | Commande type |
| --- | --- | --- |
| **`pipx`** | Poste perso (recommandé) | `pipx install --include-deps ansible` |
| **`dnf` / `apt`** | Distro stable | `sudo dnf install ansible` |
| **`mise`** | Plusieurs versions côte à côte | `mise use ansible@latest` |
| **`uv tool install`** | Alternative moderne à pipx | `uv tool install ansible` |
| **Execution Environment** | Reproductibilité totale (cible RHCE 2026) | `ansible-navigator run …` |

Vous n'avez **pas** besoin des 5 sur votre poste — une seule suffit. Mais vous devez savoir laquelle vous utilisez : ça détermine **où** Ansible est installé et **comment** le mettre à jour.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Lire `ansible --version` et identifier votre **méthode d'installation**.
2. Vérifier que les **8 binaires standard** Ansible sont dans votre `PATH`.
3. Mesurer combien de **modules** sont accessibles via `ansible-doc`.
4. Confirmer la présence des **collections clés** du repo (`ansible.posix`, `community.general`, `community.libvirt`).
5. Lancer la **vérification automatisée** du lab via `make run`.

## 🔧 Préparation

Aucune VM nécessaire — toutes les commandes tournent **sur votre poste de travail** (le control node). Placez-vous à la racine du repo :

```bash
cd /home/bob/Projets/ansible-training
```

> 💡 **Si Ansible n'est pas du tout installé** : la page du blog cite `pipx install --include-deps ansible` comme installation rapide, ou `make bootstrap` à la racine du repo qui installe la totalité de la chaîne (Ansible + outils de lint + libvirt). Lancez-la **avant** de continuer.

## 📚 Exercice 1 — Quelle version d'Ansible avez-vous ?

```bash
ansible --version
```

Sortie typique :

```text
ansible [core 2.20.1]
  config file = /home/<vous>/Projets/ansible-training/ansible.cfg
  configured module search path = ['/home/<vous>/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /home/<vous>/.local/share/pipx/venvs/ansible/lib/python3.12/site-packages/ansible
  ansible collection location = /home/<vous>/.ansible/collections:/usr/share/ansible/collections
  executable location = /home/<vous>/.local/bin/ansible
  python version = 3.12.x (...) [GCC 13.3.0] (/home/<vous>/.local/share/pipx/venvs/ansible/bin/python)
  jinja version = 3.1.6
  pyyaml version = 6.0.3 (with libyaml v0.2.5)
```

🔍 **Observation** — trois lignes à analyser :

| Ligne | Ce qu'elle vous dit |
| --- | --- |
| `ansible [core 2.x.y]` | La version d'`ansible-core`. La cible RHCE 2026 attend **`core 2.18+`** (RHEL 9/10). |
| `config file =` | Le `ansible.cfg` chargé. Doit pointer sur **celui du repo** quand vous êtes dedans (`/.../ansible-training/ansible.cfg`). Sinon, vos paramètres locaux ne s'appliqueront pas. |
| `executable location =` | Le **chemin** du binaire. Si c'est `~/.local/bin/ansible` (wrapper qui pointe vers `~/.local/share/pipx/venvs/ansible/...`) → installation pipx. Si `/usr/bin/...` → paquet distro. Si `~/.local/share/mise/shims/...` → mise. C'est ainsi qu'on identifie la méthode. |

## 📚 Exercice 2 — Les 8 binaires standard sont-ils tous présents ?

Ansible n'est pas un seul binaire : c'est une **famille de 8 commandes** que vous utiliserez tour à tour (lab 03 fait le tour). Vérifiez qu'aucune ne manque :

```bash
for bin in ansible ansible-playbook ansible-galaxy ansible-doc \
           ansible-vault ansible-config ansible-inventory ansible-lint; do
  command -v "$bin" || echo "$bin MANQUANT"
done
```

🔍 **Observation** : tous les binaires doivent retourner un chemin. Cas typiques :

- **`ansible-lint MANQUANT`** : pas livré par défaut avec `pipx install ansible`. Lancez `pipx install ansible-lint` ou `pipx inject ansible ansible-lint`.
- **`ansible-vault MANQUANT`** : suspect — `vault` est livré avec `ansible-core`, donc c'est le signe d'une installation cassée. Réinstallez Ansible.

## 📚 Exercice 3 — Combien de modules sont disponibles ?

```bash
ansible-doc -l | wc -l
```

🔍 **Observation** : vous devez obtenir **plusieurs milliers** (~10 000+). Ce nombre n'est **pas** ce que livre `ansible-core` seul (qui contient ~70 modules sous `ansible.builtin.*`) — c'est ce que livrent `ansible-core` **+ toutes les collections installées**.

- **<100 modules** : il manque des collections. Lancez `ansible-galaxy collection install -r requirements.yml` à la racine du repo.
- **~70 modules exactement** : vous êtes sur `ansible-core` pur, sans collections. Idem.

## 📚 Exercice 4 — Les collections clés sont-elles installées ?

Le repo dépend de 3 collections (déclarées dans `requirements.yml`) :

```bash
ansible-galaxy collection list | grep -E "ansible.posix|community.general|community.libvirt"
```

Sortie attendue (extrait) :

```text
ansible.posix              2.1.0
community.general          11.4.7
community.libvirt          2.2.0
```

🔍 **Observation** :

- **`ansible.posix`** : modules POSIX standard (`firewalld`, `mount`, `selinux`, `sysctl`). Indispensable pour les labs serveurs.
- **`community.general`** : très large — utilitaires (`timezone`, `archive`, `pacman`, etc.).
- **`community.libvirt`** : utilisé par l'infra de provisioning du repo (création des VMs).

Si l'une manque :

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install -r requirements.yml
```

## 📚 Exercice 5 — Vérification automatisée via Make

Le lab fournit un `Makefile` qui chaîne les 4 vérifications précédentes :

```bash
make -C labs/decouvrir/installation-ansible run
```

🔍 **Observation** : sortie attendue (extrait) :

```text
===> 1. ansible --version
ansible [core 2.20.1]
  config file = /home/.../ansible-training/ansible.cfg
  ...

===> 2. Binaires Ansible standard
  ✓ ansible
  ✓ ansible-playbook
  ✓ ansible-galaxy
  ...

===> 3. Nombre de modules disponibles
  modules disponibles : 12345

===> 4. Collections clés
ansible.posix              2.1.0
community.general          11.4.7
community.libvirt          2.2.0
```

Si une vérification échoue (binaire manquant, collection absente), corrigez **avant** d'aller au lab 03.

## 🔍 Observations à noter

- `ansible-core` ≠ `ansible` : `core` est le moteur (modules `ansible.builtin.*`), `ansible` est le metapackage qui ajoute les collections de base.
- Le `executable location =` de `ansible --version` est l'**indicateur n°1** de votre méthode d'installation. Mémorisez-le, c'est la première chose à regarder en cas de problème.
- `ansible.cfg` est cherché dans cet ordre : **(1)** variable d'env `ANSIBLE_CONFIG`, **(2)** `./ansible.cfg`, **(3)** `~/.ansible.cfg`, **(4)** `/etc/ansible/ansible.cfg`. Le premier trouvé gagne — pas de fusion. C'est pour ça qu'il faut **lancer Ansible depuis la racine du repo**.
- Une collection est **versionnée** (ex: `ansible.posix 2.1.0`). Mettre à jour Ansible n'upgrade **pas** automatiquement les collections — il faut `ansible-galaxy collection install --upgrade`.

## 🤔 Questions de réflexion

1. Vous travaillez sur 3 projets : un projet RHCE 2026 qui exige `ansible-core 2.18+`, un projet legacy qui plante au-delà de `core 2.14`, et un projet expérimental sur `core 2.20`. Quelle méthode d'installation choisissez-vous, et pourquoi ?

2. Un collègue vous dit : « Mon `ansible --version` montre `core 2.16` mais j'ai bien `pipx install ansible` dans la commande la plus récente ». Quelle est la première hypothèse à vérifier ?

3. Pourquoi est-il important que `config file =` pointe sur le `ansible.cfg` du repo, et pas sur `~/.ansible.cfg` ou `/etc/ansible/ansible.cfg` ? Quel paramètre du repo serait perdu sinon ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'écrire un script `solution.sh` qui automatise les 4 vérifications avec un **exit code clair** (0 si tout va bien, 1 sinon). C'est le genre de check qu'on poserait dans un job CI ou en pré-commit.

```bash
pytest -v labs/decouvrir/installation-ansible/challenge/tests/
```

## 💡 Pour aller plus loin

- **Tester `mise`** : créez un `.tool-versions` dans un dossier de test contenant `ansible 2.18.0`, entrez dans le dossier, et vérifiez que `ansible --version` bascule automatiquement sur cette version.
- **Tester un Execution Environment** : suivez la section EE de la page du blog pour construire un EE avec `ansible-builder` puis lancer un playbook via `ansible-navigator run playbook.yml --mode stdout`. Comparez le résultat avec votre install locale — c'est l'approche de référence pour la RHCE 2026 (reproductibilité totale via image OCI).
- **Auditer la configuration active** : `ansible-config dump --only-changed` montre uniquement les paramètres qui diffèrent des défauts. Utile pour comprendre ce que le `ansible.cfg` du repo modifie réellement.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/decouvrir/installation-ansible/lab.yml

# Lint de votre solution challenge
ansible-lint labs/decouvrir/installation-ansible/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/decouvrir/installation-ansible/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
