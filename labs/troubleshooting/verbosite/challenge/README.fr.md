# Vingt minutes à deviner, et un mot de passe dans les logs de la CI

## La situation

Une tâche échoue sur **db1.lab** avec un message qui ne dit rien d'utile, et le
réflexe de l'équipe consiste à relancer avec tous les `-v` que le clavier peut
tenir. Résultat : des milliers de lignes, et la seule qui comptait enterrée
dedans. Puis quelqu'un a vu le vrai dégât : une tâche qui manipulait un token
avait imprimé ses arguments en entier dans un log que tout le monde peut lire. La
verbosité est un scalpel, et l'équipe s'en sert comme d'un marteau, sur un playbook
à qui personne n'a demandé de se taire.

Votre mission, depuis **control-node.lab** :

1. Accorder le **niveau de verbosité au symptôme** : lequel montre les arguments
   réellement reçus par un module après templating, et lequel parle de la connexion
   SSH et n'a rien à dire sur votre bug.
2. Activer le **profilage des tâches** sur un play de trois tâches mesurables
   contre **db1.lab**, sans toucher aux tâches elles-mêmes, et lire les temps.
3. Rendre la sortie lisible : remplacer le callback du terminal par un que l'œil
   humain peut parcourir en incident, et déposer la preuve du profilage dans un
   fichier sur la cible.
4. Constater ce qu'un **`no_log` manquant** laisse fuiter en verbosité haute, et
   corriger.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/

## 🎯 Challenge — Profiler 3 tâches sur `db1.lab`

### ✅ Objectif

Écrire un playbook qui exécute **3 tâches mesurables** sur `db1.lab`, activer le callback `profile_tasks`, et déposer un fichier `/tmp/lab89-profile.txt` qui contient les **noms** des 3 tâches dans l'ordre où elles ont été exécutées.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab89-profile.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Les 3 noms de tâches séparés par `\n` (un par ligne) |
| Callbacks activés | `ansible.posix.profile_tasks` (visible dans la sortie) |

### 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-verbosite
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

Depuis la racine du repo :

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/verbosite/challenge/tests/
```

Le test pytest+testinfra valide :

- `/tmp/lab89-profile.txt` existe sur `db1.lab` avec mode `0644`.
- Le fichier contient **exactement 3 lignes** non vides (les 3 noms de tâches).
- L'`ansible.cfg` de niveau lab existe et active `ansible.posix.profile_tasks`
  (avec `callback_result_format = yaml`) : le callback qui est tout le sujet du lab.

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-verbosite
```

### 💡 Pour aller plus loin

- **Plusieurs callbacks combinés** : ajouter `ansible.posix.timer` pour le temps total.
- **Capture de timing** : rediriger la sortie `ansible-playbook` vers un fichier, parser avec `grep -E 'TASK execution time'`.
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.
