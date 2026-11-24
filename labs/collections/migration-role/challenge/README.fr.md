# Le hub n'accepte plus votre rôle, et vos utilisateurs l'ignorent

## La situation

Votre rôle standalone est publié, utilisé par des équipes que vous n'avez jamais
rencontrées, et la plateforme sur laquelle vous publiez ne prend plus que des
collections. Le rôle doit donc déménager. La contrainte : personne en aval ne
modifiera ses playbooks à votre calendrier. Ces gens appellent votre module par son
ancien nom, dans du code qui ne vous appartient pas, et un renommage qui les casse
est votre problème, pas le leur. Il faut que la migration soit invisible aujourd'hui
et assez visible pour qu'ils bougent un jour.

Votre mission, depuis **control-node.lab** :

1. Déplacer le rôle **et son module custom** dans une collection sous votre
   namespace, en plaçant chacun là où la structure d'une collection l'attend.
2. Mettre en place une **redirection** pour qu'un playbook appelant le module par
   son **ancien nom** continue de fonctionner, résolu vers le nouvel emplacement
   sans que personne n'édite quoi que ce soit.
3. Prouver que les **deux** noms marchent contre **db1.lab** : le nouveau nom
   pleinement qualifié, et l'ancien qui passe par la redirection.
4. Vérifier que le chemin hérité émet un **avertissement de dépréciation**. Une
   compatibilité silencieuse est une compatibilité éternelle, et ce n'est pas le
   contrat.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/migration-role/

## 🎯 Challenge — Migrer un rôle standalone vers une collection avec redirect

### ✅ Objectif

Migrer un rôle standalone `legacy_role` (avec un module `lab97_check`) vers la collection `student.lab97_migrated`. Configurer un **`plugin_routing.redirect`** qui maintient la rétrocompatibilité, et **prouver** que les deux noms fonctionnent.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab97-migration.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Une ligne `legacy: lab97-migrated-OK` (appel par l'ancien nom) **et** une ligne `new: lab97-migrated-OK` (appel par le nouveau FQCN) |
| Collection cible | `student.lab97_migrated` (namespace `student`, name `lab97_migrated`) |
| Module migré | `plugins/modules/lab97_check.py` |
| `plugin_routing` | redirect `lab97_status` → `student.lab97_migrated.lab97_check` |
| Deprecation warning | présent au runtime |

> ⚠️ **La route part de l'ANCIEN nom.** Le module s'appelait `lab97_status`
> dans le `library/` du rôle standalone ; il s'appelle `lab97_check` dans la
> collection. La clé de `plugin_routing.modules` est le nom à faire survivre,
> la cible est le nom réel. **Les deux doivent différer** : une entrée
> `lab97_check: {redirect: student.lab97_migrated.lab97_check}` se redirige
> vers elle-même, et ansible-core la rejette au runtime avec
> `plugin redirect loop resolving lab97_check`.
>
> Aucun fichier `plugins/modules/lab97_status.py` ne doit exister : si l'ancien
> nom répond, c'est **la redirection** qui l'a résolu, et rien d'autre. C'est
> exactement ce que les tests vérifient.

### 🧩 Bloqué ?

```bash
dsoxlab hint collections-migration-role
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/collections/migration-role/
ANSIBLE_COLLECTIONS_PATH=challenge/ansible_collections \
  ansible-playbook challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/collections/migration-role/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean collections-migration-role
```

### 💡 Pour aller plus loin

- **`ANSIBLE_DEPRECATION_WARNINGS=False`** pour tester en CI sans bruit.
- **`ansible-lint --profile production`** doit retourner vert sur la collection cible.
- **Antsibull-changelog** : générer un `CHANGELOG.rst` qui mentionne la migration comme `breaking_changes` (au bump majeur).
