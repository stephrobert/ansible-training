# Un bug remonté depuis une version que vous n'avez jamais lancée

## La situation

Une issue tombe sur votre rôle publié : il échoue sur `ansible-core` 2.19. Vous
n'arrivez pas à reproduire, parce que votre poste tourne en 2.21 et n'a jamais
fait autrement. Vos utilisateurs, eux, sont ailleurs : certains sont figés sur
la LTS par leur équipe plateforme, d'autres sont déjà sur la dernière version, et
votre suite mono-version est aveugle aux deux. Reproduire à la main impose de
reconstruire un virtualenv par version, et personne dans l'équipe ne le fera deux
fois.

Votre mission, depuis le répertoire du projet :

1. Déclarer un environnement **par version d'`ansible-core`** à supporter, chacun
   isolé et épinglant la sienne, pour qu'aucune version ne déborde sur l'autre.
2. Faire lancer à chaque environnement le cycle Molecule complet sur le même
   rôle, pour que « ça passe » veuille dire la même chose partout.
3. Rendre toute la matrice jouable en **une seule commande**, et une version
   précise ciblable à la demande quand vous traquez un échec particulier.
4. Lire le verdict : une divergence entre environnements est un bug de
   portabilité du rôle, pas un test instable.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/

## 🎯 Challenge : écrire le tox.ini multi-versions

### ✅ Mission

Le fichier `tox.ini` est livré en **squelette**. Écrivez la configuration
qui teste le rôle `webserver` sur plusieurs versions d'ansible-core.

État attendu (c'est ce que pytest vérifie) :

| Élément | Attente |
| --- | --- |
| `[tox] envlist` | syntaxe range `ansible2.{...}` couvrant au moins 3 versions récentes d'ansible-core |
| `[testenv]` | `commands` lance `molecule test` |
| `[testenv:ansible-X]` | au moins 3 sections, chacune épinglant `ansible-core` dans ses `deps` |
| `[testenv:lint]` | environnement séparé pour yamllint + ansible-lint (fail-fast, sans monter d'instance) |

### 🧩 Bloqué ?

```bash
dsoxlab hint tests-tox-multiversion
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand votre configuration est prête, consignez dans `challenge/solution.sh`
les commandes tox exécutées. Ce journal doit exister pour que pytest
s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/tests/tox-multiversion/challenge/tests/
```

Le test parse votre tox.ini (sémantique des sections) et, si tox est
installé sur le poste, exécute `tox --listenvs` pour prouver que la
configuration est acceptée par l'outil.

### 🧹 Reset

```bash
dsoxlab clean tests-tox-multiversion
```

### 💡 Pour aller plus loin

- `tox -p auto` : exécuter les environnements en parallèle.
- `tox-uv` : résolution des deps beaucoup plus rapide.
- Croiser avec la matrice CI du lab 69 : tox local, matrice GitHub distante.
