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

## Attester un lab dans les deux sens

`dsoxlab check` dit si un travail passe les tests ; il ne dit pas si les tests
**échouent avant le travail**. Un lab vert sur son état de départ ne mesure
rien. `scripts/valider-labs.py` exige les deux : un lab doit rendre **0 avant
le travail** et réussir **tous ses tests après la solution de référence**, puis
il écrit le verdict daté dans `validation-labs.json`, le relevé qu'affiche le
site.

```bash
mise exec -- python3 scripts/valider-labs.py --lab <id-du-lab>   # répétable
mise exec -- python3 scripts/valider-labs.py --section vault
python3 scripts/valider-labs.py --check     # échoue si un verdict est ROUGE
```

C'est un outil de **formateur** : il déchiffre les solutions, donc il exige
`.vault-pass`, et il exige les quatre VM debout avec leur base figée. Avant
chaque lab VM, il ramène ses machines à cette base (l'isolation du
`conftest.py`) : sans cela, le premier check noterait aussi ce qu'ont laissé
les labs joués avant lui. La base se fige après chaque `provision`, qui
recrée les domaines :

```bash
mise run provision
mise run rebase
```

Le premier check se joue **sans `.vault-pass`**, écarté le temps de ce seul
check, parce que le `conftest.py` retombe sur la solution de référence quand il
la trouve : l'apprenant, lui, ne l'a jamais. Un lab qui laisse un conteneur, un
fichier versionné modifié ou une solution dans `challenge/` est ROUGE. Un
`challenge/solution.yml` déjà présent bloque le lab : c'est un travail en
cours, le script n'y touche pas.

## Conventions

- **Id de lab :** `<section>-<slug>` (ex. `decouvrir-installation-ansible`), pour
  un répertoire `labs/<section>/<slug>/`.
- **Commits :** `feat(<lab>): …`, `fix: …`, `docs: …`, `test: …`.
- **i18n :** `lab.fr.yaml` surcharge le `title` et la `description` uniquement.

## Pull requests

Travaille sur une branche dédiée, garde `dsoxlab validate-structure` vert, écris
une description claire et relie la capacité ou l'issue traitée.
