# Lab 84 — Hello Execution Environment

> 💡 **Pré-requis** :
> - **Podman** installé (`podman --version`).
> - **ansible-navigator** installé (`pipx install ansible-navigator`).
> - 4 VMs lab joignables (`ansible all -m ansible.builtin.ping` répond `pong`).

## 🧠 Rappel

🔗 [**Présentation des Execution Environments**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/)

Un **Execution Environment (EE)** est une **image conteneur OCI** qui empaquette `ansible-core`, `ansible-runner`, des **collections** Ansible, des **dépendances Python** et des **dépendances système**. L'EE garantit que le **même runtime** Ansible tourne du laptop au controller AAP — fini le « ça marche sur mon poste ».

**Ansible Navigator** lance un playbook **dans un EE** au lieu de l'exécuter directement avec `ansible-playbook`. Bénéfices : **isolation**, **reproductibilité**, **debug riche** (TUI ou stdout, artifacts JSON, replay).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Vérifier** que Podman et ansible-navigator sont installés.
2. **Tirer** une image EE (`quay.io/ansible/creator-ee:latest`).
3. **Configurer** `ansible-navigator.yml` avec un EE par défaut.
4. **Lancer** un premier playbook dans l'EE (mode `stdout` et mode interactif).
5. Comparer **`ansible-playbook`** classique vs **`ansible-navigator run`**.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/ee/hello/

# Vérifier les outils requis
./setup-ee.sh
```

## ⚙️ Arborescence cible

```text
labs/ee/hello/
├── README.md
├── setup-ee.sh                     ← vérifie podman + ansible-navigator
├── inventory.yml                    ← inventaire 3 VMs lab
├── ping.yml                         ← playbook de démo (ansible.builtin.ping)
├── ansible-navigator.yml            ← config EE par défaut + mode stdout
└── challenge/
    └── tests/
        └── test_ee_hello.py        ← tests structurels (6 tests)
```

## 📚 Exercice 1 — Pull de l'image EE

```bash
podman pull quay.io/ansible/creator-ee:latest
podman images | grep creator-ee
```

Sortie typique :

```text
quay.io/ansible/creator-ee  latest  abc123def  3 days ago  1.2 GB
```

🔍 **Observation** : l'image fait **~1 Go** car elle embarque ansible-core, ansible-runner, ansible-lint, ansible-navigator, et de nombreuses collections (`ansible.posix`, `community.general`, `community.kubernetes`...). C'est l'**EE communautaire le plus complet** — idéal pour la formation et le dev.

## 📚 Exercice 2 — Lancer un playbook avec ansible-navigator (mode stdout)

```bash
ansible-navigator run ping.yml \
  -i inventory.yml \
  --eei quay.io/ansible/creator-ee:latest \
  -m stdout
```

Sortie attendue :

```text
PLAY [Lab 84 — Premier run avec ansible-navigator + EE] *********

TASK [Ping via le module ansible.builtin.ping] *****
ok: [db1.lab]
ok: [web1.lab]
ok: [web2.lab]

PLAY RECAP *****************************************
db1.lab  : ok=1  changed=0  unreachable=0  failed=0
web1.lab : ok=1  changed=0  unreachable=0  failed=0
web2.lab : ok=1  changed=0  unreachable=0  failed=0
```

🔍 **Observation** : la sortie ressemble à `ansible-playbook` classique. La différence : **Ansible tourne dans un conteneur Podman éphémère**. Vérifiez avec `podman ps -a` — le conteneur a disparu, c'est volontaire (éphémère).

## 📚 Exercice 3 — Mode interactif (TUI)

```bash
ansible-navigator run ping.yml \
  -i inventory.yml
# (sans -m stdout)
```

L'interface TUI s'ouvre :

- **Menu numéroté** : tapez `0` pour voir les plays, `1` pour voir les tasks, `2` pour les hosts.
- **Drill-down** : sélectionnez une task, voyez le résultat host par host, le retour JSON brut, le diff.
- **Navigation clavier** : flèches, `Esc` pour remonter, `:q` pour quitter.

🔍 **Observation** : la TUI sert au **debug riche** — drill-down task → host → résultat JSON. Idéal en formation et en debug local. **Pas adaptée au CI/CD** où on préfère `-m stdout`.

## 📚 Exercice 4 — Configuration `ansible-navigator.yml`

Le fichier `ansible-navigator.yml` du lab contient la configuration par défaut :

```yaml
ansible-navigator:
  execution-environment:
    image: quay.io/ansible/creator-ee:latest
    container-engine: podman
  mode: stdout
```

Avec ce fichier, on peut simplifier la commande :

```bash
ansible-navigator run ping.yml -i inventory.yml
# → utilise creator-ee + mode stdout par défaut
```

🔍 **Observation** : `ansible-navigator.yml` est cherché dans **`./ansible-navigator.yml`**, **`~/.ansible-navigator.yml`**, ou via **`$ANSIBLE_NAVIGATOR_CONFIG`**. Permet de figer l'EE et le mode pour un projet entier.

## 📚 Exercice 5 — Comparaison ansible-playbook vs ansible-navigator

```bash
# Classique (sur le venv local)
time ansible-playbook ping.yml -i inventory.yml

# Avec EE
time ansible-navigator run ping.yml -i inventory.yml -m stdout
```

| Critère | `ansible-playbook` | `ansible-navigator run` |
|---------|--------------------|-------------------------|
| Démarrage | Immédiat (~0.5 s) | +1-3 s (lancement Podman) |
| Reproductibilité | Selon venv local | EE figé, identique partout |
| Collections | Celles du venv | Celles de l'EE |
| Debug | `-vvv` texte | TUI + artifacts JSON |
| CI/CD | Setup Python + collections | `podman run` + image EE |

🔍 **Observation** : **navigator** ajoute ~1-3 s par run (overhead Podman) en échange de la **reproductibilité**. Pour itération dev rapide : `ansible-playbook`. Pour prod, formation, CI/CD : `ansible-navigator`.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible votre poste local ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi la première exécution avec navigator est-elle plus lente ? (Indice : `podman pull`).

2. Un développeur utilise `ansible-playbook` localement, un autre utilise `ansible-navigator` avec un EE. **Quel risque** introduit cette divergence ?

3. Comment **forcer** ansible-navigator à utiliser **Docker** au lieu de Podman ? Et pourquoi le ferait-on ?

4. À quoi sert `volume-mounts` dans `ansible-navigator.yml` ? Que se passe-t-il sans pour les clés SSH ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide la structure du lab via 6 tests pytest (script setup, inventaire valide, ansible-navigator.yml correct).

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Lab 85** : inspecter un EE (collections, ansible-core version, Python deps).
- **Lab 86** : construire son propre EE avec `ansible-builder`.
- **Configuration `ansible-navigator.yml` complète** : `playbook-artifact.enable`, `logging`, `time-zone`, `lint.config`.
- **Variables d'environnement** : `ANSIBLE_NAVIGATOR_EE_IMAGE`, `ANSIBLE_NAVIGATOR_MODE`.
- **EE Red Hat AAP** : `registry.redhat.io/ansible-automation-platform-25/ee-supported-rhel9` (Subscription).

## 🔍 Sécurité — bonnes pratiques 2026

- **Image pinnée** : `creator-ee:v25.5.0` plutôt que `:latest` en prod.
- **Volume-mounts SSH** en `ro,Z` (lecture seule + label SELinux).
- **Pas de secret en variable d'env du conteneur** : passer via `--vault-password-file` ou un secret manager.
- **`pull.policy: missing`** en dev (rapide), **`always`** en CI (toujours la dernière version).
- **Signature image** : vérifier avec `cosign verify` avant de pull en prod.
