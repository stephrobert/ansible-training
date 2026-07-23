# Contribuer à ansible-training

**Langue :** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

Ce dépôt est un **catalogue de labs** consommé par la CLI
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Les contributions sont de
nouveaux labs, des correctifs et des traductions. La CLI vit dans son propre
dépôt : n'ajoute pas de code moteur ici.

> **Migration en cours.** Le catalogue passe actuellement au contrat dsoxlab
> 0.1.6 (`lab.yaml` par lab, `setup.yaml` / `cleanup.yaml`, infra déclarée dans
> `meta.yml`). Ce document décrit le contrat cible. Tant que la migration n'est
> pas terminée, les contributions de nouveaux labs sont mises en attente :
> ouvre une issue plutôt qu'une PR, on cale le périmètre ensemble.

## Mise en place

```bash
uv tool install dsoxlab        # la CLI (outil externe)
git clone <url-de-ce-depot> ansible-training
cd ansible-training
dsoxlab doctor                 # vérifier l'environnement
dsoxlab provision              # monter les managed nodes du lab
```

## La règle d'or : la validation prouve l'état

Les tests d'un lab doivent vérifier **l'état des managed nodes**, jamais qu'un
playbook a été écrit ni qu'une commande a été tapée. Le service tourne **et** est
activé ; le fichier déployé a le bon contenu **et** le bon propriétaire ; le
paquet est installé **et** le dépôt est déclaré.

Deuxième exigence, propre à Ansible : **l'idempotence**. Un lab dont le playbook
de solution rejoué une seconde fois annonce encore des `changed` est un lab
faux. C'est le piège qui fait échouer les candidats RHCE : les tests doivent le
prouver, pas l'espérer.

## Anatomie d'un lab

```text
labs/<section>/<lab>/
├── lab.yaml            # le contrat (id, level, runtime, validation…)
├── lab.fr.yaml         # optionnel : surcharge FR du title/description UNIQUEMENT
├── README.md
├── scenario.md         # scenario.fr.md pour la version française
├── setup.yaml          # état de départ posé sur les managed nodes
├── cleanup.yaml        # remise à zéro entre deux passages
└── challenge/
    ├── README.md       # la mission, sans pas-à-pas
    ├── hints.yaml      # indices à coût variable
    └── tests/test_functional.py    # la preuve : l'état du système
solution/…              # solution de référence, chiffrée via ansible-vault
```

Les playbooks ciblent les groupes que dsoxlab injecte dans l'inventaire :
`lab_target` pour l'hôte principal, `lab_<role>` pour chaque rôle déclaré dans
`runtime.targets[].roles`. Ne code jamais un FQDN en dur.

## Proposer un lab

- **Partir d'une capacité, pas d'un module.** Décris une capacité démontrable
  (« déployer un vhost et prouver qu'il survit à un rejeu du playbook »), ouvre
  une issue, et cale le périmètre avant d'écrire.
- **Choisir le runtime qu'impose le sujet :** `vm` dès qu'il faut de vrais
  managed nodes (services, paquets, utilisateurs, réseau, stockage) ; `shell`
  seulement pour ce qui reste local au control node (écrire du YAML, un template
  Jinja2, un inventaire).
- Fais pointer `doc_url` vers le vrai guide que le lab fait pratiquer.

## Les solutions restent chiffrées

Les solutions de référence vivent dans `solution/`, **chiffrées avec
`ansible-vault`**. Ne commite jamais une solution en clair, ni le fichier
`.vault-pass`. Une solution en clair dans une PR est un motif de refus
automatique : elle spoile le lab pour tout le monde.

## Vérifications locales (avant d'ouvrir une PR)

```bash
dsoxlab list-labs              # ton lab apparaît-il ? sinon, lab.yaml invalide
dsoxlab validate-structure     # le contrat meta.yml + lab.yaml
dsoxlab check <id-du-lab>      # lancer les tests du lab
ansible-lint                   # profil production (cf. .ansible-lint)
```

Dans cet ordre, et `list-labs` en premier : un `lab.yaml` qui lève au parsing
disparaît **silencieusement** du catalogue, et `validate-structure` ne valide que
les labs déjà découverts. Un lab absent de `list-labs` est presque toujours un
`lab.yaml` invalide.

## Conventions

- **Id de lab :** `<section>-<slug>` (ex. `decouvrir-installation-ansible`), pour
  un répertoire `labs/<section>/<slug>/`.
- **Commits :** `feat(<lab>): …`, `fix: …`, `docs: …`, `test: …`.
- **i18n :** `lab.fr.yaml` surcharge le `title` et la `description` uniquement.

## Pull requests

Travaille sur une branche dédiée, garde `dsoxlab validate-structure` vert, écris
une description claire et relie la capacité ou l'issue traitée.
