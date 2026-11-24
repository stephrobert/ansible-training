# Quatre-vingt-dix tâches à rejouer pour corriger un mot

## La situation

Le play de déploiement meurt à la tâche 91 sur **db1.lab** : une variable non
définie, et aucun moyen de savoir ce qu'elle aurait dû valoir. Alors vous devinez,
vous éditez le YAML, et vous relancez tout depuis le début. Quatre-vingt-dix
tâches, douze minutes, mauvaise pioche. Deuxième tentative : quatre-vingt-dix
tâches, douze minutes. Chaque itération d'une correction d'un mot coûte une pause
café, et le run ne vous laisse jamais regarder autour de vous à l'instant précis
où il sait quelque chose.

Votre mission, depuis **control-node.lab** :

1. Armer le play pour qu'une tâche en échec **ouvre une session au lieu de tuer le
   run**, à l'endroit exact où l'état est encore disponible.
2. Depuis là, inspecter ce que le run sait : la tâche telle qu'elle a été résolue,
   les variables dans la portée, et le résultat du module lui-même.
3. Corriger la panne **à chaud**, en fournissant la valeur manquante dans la
   session vivante plutôt que dans le fichier, et **rejouer cette seule tâche**
   pour valider votre hypothèse.
4. Une fois le run terminé, inscrire proprement la correction dans le playbook,
   pour que la valeur ne dépende plus de quelqu'un devant son clavier.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/

## 🎯 Challenge — Fix d'une variable manquante via le débogueur

### ✅ Objectif

Écrire un playbook qui **échoue volontairement** sur une variable `target_dir` non définie, puis utiliser le **débogueur Ansible** pour **injecter la variable au runtime** (`task_vars['target_dir'] = '/tmp'`) et faire passer la tâche **sans modifier le YAML**.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab90-debug.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | "Debugger fix au runtime — lab 90 OK" |
| Mécanisme | `debugger: on_failed` activé sur la task qui copie |

> ⚠️ **Mode interactif** : ce challenge nécessite un terminal interactif.
> Pour la **validation pytest**, le `solution.yml` final doit avoir
> `target_dir` correctement défini en `vars:` (pas la version cassée
> avec débogueur — pytest tournera après votre fix).

### 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-debugger
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/troubleshooting/debugger/challenge/solution.yml
```

(la version finale **avec** `vars: { target_dir: /tmp }`, sans débogueur).

### 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/debugger/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-debugger
```

### 💡 Pour aller plus loin

- Activer le débogueur **globalement** : `ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook lab.yml`.
- `debugger: always` : ouvre le REPL **après chaque tâche** (lent, utile en TDD).
- **`ansible-lint`** : `ansible-lint --profile production challenge/solution.yml` doit retourner vert.
