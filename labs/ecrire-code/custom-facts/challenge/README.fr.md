# L'hôte qui doit dire à qui il appartient

## La situation

La moitié du parc n'a pas de propriétaire. Quand une machine déraille à
2 heures du matin, l'ingénieur d'astreinte doit deviner quelle équipe
réveiller, et la seule réponse vit dans une page de wiki vieille d'un an.
L'inventaire ne peut pas aider : il décrit ce qu'Ansible gère, pas ce que la
machine porte. Donc la machine va le dire elle-même, et Ansible le relira à
chaque run, à côté des facts qu'il collecte déjà. Vous commencez par
**db1.lab**, depuis **control-node.lab**.

Votre mission :

1. Déposer sur db1 un **custom fact INI statique** déclarant le projet auquel
   il appartient, sa version, et l'équipe qui en est propriétaire.
2. Déposer un second fact qui est un **script exécutable retournant du JSON** :
   ce qu'aucun fichier statique ne peut savoir, comme le noyau courant et
   l'uptime.
3. Poser les bons modes : un fact statique se lit, un fact dynamique doit être
   **exécutable**. Le mauvais mode est l'échec classique ici, et son message
   d'erreur ne vous aidera pas.
4. Re-collecter les facts, puis relire les deux via **`ansible_local`** et
   écrire le fichier de preuve sur db1.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/

## 🎯 Challenge — Combiner custom facts INI + script Bash

### ✅ Objectif

Déposer **deux** custom facts sur `db1.lab` (un INI statique + un script Bash dynamique), puis dans un playbook **lire les deux** et écrire un fichier preuve qui combine les valeurs.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (script Bash, mode `0755`) |
| Fichier produit | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Valeurs des 2 facts (au moins 4 lignes) |

### 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-custom-facts
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-custom-facts
```

### 💡 Pour aller plus loin

- **Custom path** : `setup -a "fact_path=/custom/path"` pour ne pas utiliser le défaut `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** doit retourner vert.
