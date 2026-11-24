# Votre automatisation ne tient plus dans un rôle

## La situation

L'automatisation partagée de l'équipe a dépassé ce qu'un rôle peut porter. Il y a
un rôle nginx, un module Python écrit par quelqu'un pour contrôler la santé de
l'application, et trois playbooks qui relient le tout, chacun dans son dépôt, avec
sa version, et aucune version de l'ensemble. Les utilisateurs installent trois
choses et espèrent que la combinaison tient. Par ailleurs, la plateforme sur
laquelle l'entreprise publie n'accepte plus du tout les rôles standalone.

Votre mission, depuis **control-node.lab** :

1. Générer une **collection** sous votre namespace et renseigner son manifeste :
   namespace, nom, version, dépendances et tags. Voilà la nouvelle unité versionnée.
2. Y intégrer un **rôle**, et ajouter votre propre **module Python**, avec la
   documentation, les exemples et le bloc de retour qu'un module doit porter.
3. Rendre compte de la structure standard : ce qui va dans plugins, roles,
   playbooks, meta et tests, et pourquoi un module ne se dépose pas n'importe où.
4. **Builder le tarball** et vérifier que la collection passe les contrôles de
   sanity : une collection qui échoue en sanity n'est pas distribuable.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/creer-collection-custom/

## 🎯 Challenge — Initialiser et builder votre collection minimaliste

### ✅ Objectif

Initialiser une collection **`student.lab95`**, y ajouter **un module Python** qui retourne `"Hello, lab95!"`, builder le tarball, et prouver que la structure passe `ansible-test sanity --docker default --test ansible-doc`.

| Élément | Valeur attendue |
| --- | --- |
| Namespace | `student` |
| Nom collection | `lab95` |
| Version | `1.0.0` |
| Module custom | `plugins/modules/lab95_hello.py` qui retourne `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| Tags `galaxy.yml` | au moins `[demo, lab95]` |

### 🧩 Bloqué ?

```bash
dsoxlab hint collections-creer-custom
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/collections/creer-custom/challenge/
# Suivez les étapes ci-dessus pour produire build/student-lab95-1.0.0.tar.gz
```

### 🧪 Validation automatisée

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

Le test pytest valide la **structure générée** : tarball présent, galaxy.yml conforme, module Python avec `DOCUMENTATION` + `EXAMPLES` + `RETURN`.

### 🧹 Reset

```bash
dsoxlab clean collections-creer-custom
```

### 💡 Pour aller plus loin

- **`ansible-test sanity --docker default --test ansible-doc`** dans la collection.
- **`ansible-galaxy collection publish ...`** vers Galaxy (token API requis).
- **`changelogs/fragments/`** : un YAML par PR plutôt qu'un CHANGELOG.rst monolithique.
