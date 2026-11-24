# La revue qui rejoue toujours la même dispute

## La situation

Chaque merge request sur les rôles de l'équipe rouvre le même débat : noms de
modules courts, tâches sans `name:`, un `shell:` là où un module dédié existe,
`yes` au lieu de `true`. Les relecteurs en ont assez de servir de linter. Et le
mois dernier, quelqu'un a commité une clé privée : elle est restée trois jours
dans l'historique avant que personne ne le remarque. Le style se négocie en
revue ; une clé qui fuit, non. Les deux relèvent d'une machine, et cette machine
doit dire non avant que le commit existe.

Votre mission, depuis le répertoire du projet :

1. Épingler le linter sur son **profil le plus strict**, celui qu'on exige d'un
   code livré en production, et écouter ce qu'il dit du rôle tel qu'il est.
2. Ajouter par-dessus une politique YAML stricte : les booléens ambigus et le
   formatage approximatif cessent de passer en revue parce qu'ils cessent de
   passer l'outil.
3. Câbler les deux dans un **hook Git** joué à chaque commit, pour qu'aucun code
   non conforme n'atteigne la branche et que la CI ne fasse que confirmer.
4. Ajouter un hook qui **bloque les fuites de secrets** dès le commit, clés
   privées comprises.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-lint-production-profile/

## 🎯 Challenge : mettre un rôle au niveau du profil production

### ✅ Mission

Le rôle `roles/webserver` est livré **volontairement fautif** : il
fonctionne, mais `ansible-lint --profile production` y relève une bonne
dizaine de violations (FQCN manquants, tâche sans nom, mode octal risqué,
`ignore_errors`, `shell` à la place d'un module...). Les fichiers de
configuration lint sont livrés en squelette.

Votre travail, en deux temps :

1. **Écrire la configuration** : `.ansible-lint` (profil production,
   exclusions), `.yamllint` (truthy strict), `.pre-commit-config.yaml`
   (hooks de base + yamllint + ansible-lint).
2. **Corriger le rôle** jusqu'à ce que `ansible-lint --profile production
   roles/` retourne 0, **sans changer son comportement** (mêmes paquets,
   même service, même page déployée).

Pytest exécute réellement `ansible-lint --profile production` : le lab
n'est validé que quand le linter est vert.

### 🧩 Bloqué ?

```bash
dsoxlab hint tests-ansible-lint-production
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand tout est vert, consignez dans `challenge/solution.sh` les commandes
exécutées (`ansible-lint ...`, `yamllint roles/`, `pre-commit run
--all-files`). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/tests/ansible-lint-production/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean tests-ansible-lint-production
```

### 💡 Pour aller plus loin

- `pre-commit install` : rendre le commit impossible tant que le lint échoue.
- `ansible-lint --fix` : corrections automatiques (à relire avant commit).
- Brancher ce même profil dans la CI du lab 69.
