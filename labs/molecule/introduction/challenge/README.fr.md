# « ça marche chez moi » n'est pas un rapport de test

## La situation

Le rôle `webserver` passe sur votre poste et casse sur celui de votre collègue.
Chaque revue se termine pareil : quelqu'un affirme que le rôle est bon, personne
ne peut le prouver, et la seule façon de vérifier consiste à brûler une VM pour
regarder le résultat à l'œil. Avant d'automatiser quoi que ce soit, l'équipe a
besoin d'un harnais de test lisible et fiable, et d'un vocabulaire commun sur ce
que « testé » veut dire.

Votre mission, depuis le répertoire du projet :

1. Ouvrir le scénario livré dans `molecule/default/` et rendre compte de chacun
   de ses trois fichiers : qui crée l'instance, qui applique le rôle, qui juge
   le résultat.
2. Identifier le **driver** (sur quoi tourne l'instance), les **plateformes**
   (quelles instances sont créées) et le **verifier** (qui prononce le verdict).
3. Dérouler le cycle complet, de la création à la destruction, et situer l'étape
   d'**idempotence** : ce qu'elle rejoue, et ce qu'un échec à ce stade signifie.
4. Confirmer que le scénario est conforme au standard, et pas juste présent.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tdd-molecule-introduction/

## 🎯 Challenge : écrire votre premier scénario Molecule

### ✅ Mission

Le rôle `webserver` est livré complet dans `roles/`. Le scénario Molecule,
lui, est livré en **squelette** : `molecule/default/{molecule.yml,
converge.yml, verify.yml}` contiennent des `???` et des listes vides.
Complétez les trois fichiers pour obtenir un scénario fonctionnel.

`create.yml`, `destroy.yml` et `prepare.yml` sont **fournis** : c'est le
banc de test, pas l'exercice. Ils méritent quand même une lecture, car ils
expliquent le point le moins intuitif de Molecule v6+ : le driver `default`
est **délégué**, il ne parle ni à Podman ni à Docker. Ce sont ces playbooks
qui montent réellement l'instance en appelant `containers.podman`. Sans
eux, Molecule sauterait l'étape `create` sans broncher et le `converge`
irait frapper à la porte d'une machine qui n'existe pas.

État attendu (c'est ce que pytest vérifie) :

| Fichier | Attente |
| --- | --- |
| `molecule.yml` | `driver` valide, au moins 1 plateforme, `verifier` déclaré |
| `converge.yml` | applique le rôle `webserver` avec `become: true` |
| `verify.yml` | au moins 2 tâches `ansible.builtin.assert` qui prouvent l'état (paquet nginx, nginx.conf) |
| Le tout | `molecule syntax` passe (pytest l'exécute réellement) |

### 🧩 Bloqué ?

```bash
dsoxlab hint molecule-introduction
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Quand votre scénario est prêt, consignez dans `challenge/solution.sh` les
commandes Molecule que vous avez exécutées. Ce journal doit exister pour
que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/introduction/challenge/tests/
```

Le test charge vos trois fichiers YAML, contrôle leur sémantique, puis
lance réellement `molecule syntax`.

### 🧹 Reset

```bash
dsoxlab clean molecule-introduction
```

### 💡 Pour aller plus loin

- Lab 63 : enrichir la config (prepare.yml, requirements.yml, test_sequence).
- Lab 64 : cycle TDD complet sur un nouveau rôle.
- Lab 65 : multi-distro (RHEL + Debian + Ubuntu).
