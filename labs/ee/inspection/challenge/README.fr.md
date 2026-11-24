# Quelqu'un a choisi un EE parce qu'il sortait en premier

## La situation

Le projet s'est standardisé sur un Execution Environment le trimestre dernier,
choisi comme souvent : quelqu'un a trouvé un nom d'image dans un article de blog
et ça marchait. Il pèse deux gigaoctets, embarque des collections que personne
n'utilise, et il manque toujours celle dont vos playbooks ont besoin, qu'un
collègue installe désormais au runtime dans le conteneur, ruinant discrètement
tout l'intérêt de la démarche. Avant de construire le vôtre, il faut savoir dire
ce qu'il y a vraiment dans ces images.

Votre mission, depuis le répertoire du projet :

1. Scripter l'inspection d'un EE : **lister les collections embarquées**, la
   version d'`ansible-core` transportée, les paquets système et la taille réelle.
2. Passer cette inspection sur **trois** EE officiels, l'un orienté création, l'un
   orienté controller, l'un délibérément minimal, et comparer les résultats.
3. Lire la documentation d'un module **telle que l'EE la voit** : ce qui est
   documenté dans l'image est ce que votre playbook pourra réellement appeler.
4. Convertir la comparaison en **choix par cas d'usage** : quel EE pour la
   formation, lequel pour un controller, lequel pour une production sobre, et
   pourquoi.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/lookup-doc/

## 🎯 Challenge : comparer 3 Execution Environments, preuves à l'appui

### ✅ Mission

Écrire `inspect.sh` (livré en squelette à la racine du lab), l'exécuter,
et produire un rapport de comparaison factuel.

| Livrable | Attente |
| --- | --- |
| `inspect.sh` | complété (plus de `???`), exécutable, syntaxe bash valide. Inspecte les 3 EE `community-ansible-dev-tools`, `awx-ee`, `community-ee-minimal` avec podman et ansible-navigator |
| `inspect-output/comparison.md` | généré par VOTRE script : un tableau Markdown avec, pour chacun des 3 EE, la version d'ansible-core constatée et la taille d'image |

Le rapport doit venir de l'exécution réelle du script (`./inspect.sh`),
pas d'un copier-coller : les versions constatées changent avec les tags
`latest`, c'est justement l'intérêt de l'inspection.

### 🧩 Bloqué ?

```bash
dsoxlab hint ee-inspection
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
cd labs/ee/inspection/
./inspect.sh
cat inspect-output/comparison.md
```

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées. Ce journal
doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/inspection/challenge/tests/
```

Pytest vérifie votre script (syntaxe bash réelle, outils utilisés, 3 EE
couverts) et le contenu factuel du rapport généré. Il ne tire pas les
images lui-même (plusieurs Go) : c'est votre exécution qui produit le
rapport.

### 🧹 Reset

```bash
dsoxlab clean ee-inspection
```

### 💡 Pour aller plus loin

- `skopeo inspect docker://<ee>` : métadonnées sans pull complet.
- Choisir son EE : minimal pour lab et démos, awx-ee pour AWX/AAP,
  community-ansible-dev-tools pour le développement de collections.
