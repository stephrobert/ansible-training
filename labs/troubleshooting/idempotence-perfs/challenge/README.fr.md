# Du jaune à chaque run, et plus personne ne lit le recap

## La situation

Le play nocturne annonce `changed=14` toutes les nuits, sur des hôtes où rien n'a
bougé depuis des semaines. Les tâches refont le
travail, elles invalident des caches, et elles ont appris à l'équipe à ignorer le
recap. C'est précisément pour cela que le vrai changement de mardi dernier est
passé inaperçu pendant trois jours. Par-dessus le marché, le play met onze minutes,
et la direction commence à demander pourquoi.

Votre mission, depuis **control-node.lab** :

1. Refondre les trois opérations fautives sur **db1.lab** pour que le play affiche
   **`changed=0` au second passage** : une commande brute qui ne doit pas se
   rejouer, une ligne de configuration qui doit être reconnue plutôt qu'ajoutée, et
   une lecture seule qui n'a rien à faire dans les changements.
2. Prouver la correction de la seule façon qui compte : lancer deux fois et lire le
   recap.
3. Mesurer un **point de référence** avant d'optimiser : nommer les tâches qui
   coûtent réellement les onze minutes, plutôt qu'optimiser par tradition orale.
4. Régler ensuite la couche de connexion : moins d'allers-retours par tâche, plus
   d'hôtes en parallèle (la connexion SSH est déjà réutilisée par défaut grâce à
   `ControlPersist`). Remesurer et annoncer le gain réel.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/

## 🎯 Challenge — Refactorer un playbook non idempotent

### ✅ Objectif

Écrire un playbook qui **passe le test d'idempotence** : `changed=0` au second passage. Trois opérations à enchaîner sur `db1.lab`, chacune **idempotente** :

| # | Action | Module recommandé | Garde idempotence |
| --- | --- | --- | --- |
| 1 | Créer `/tmp/lab91-marker` avec contenu | `ansible.builtin.shell` | `creates:` |
| 2 | Poser `max_connections = 200` dans `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Lire la version curl et la stocker dans `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` sur la lecture |

**Critère** : second passage de `solution.yml` retourne `changed=0`.

### 🧩 Bloqué ?

```bash
dsoxlab hint troubleshooting-idempotence-perfs
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-idempotence-perfs
```

### 💡 Pour aller plus loin

- **`ansible-lint --profile production`** détecte les `command`/`shell` sans `changed_when:`.
- **Pre-commit hook `ansible-lint`** dans le repo pour bloquer les régressions.
- **Mode `--check --diff`** pour prévisualiser les changements sans appliquer.
