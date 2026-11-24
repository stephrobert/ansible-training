# Des tests écrits après le code sont toujours d'accord avec le code

## La situation

Les rôles de l'équipe sont tous testés, et les tests n'attrapent jamais rien.
L'historique Git dit pourquoi : les tâches sont écrites d'abord, les assertions
ensuite, et elles finissent par décrire ce que le code fait plutôt que ce qu'on
avait demandé. Vous démarrez un nouveau rôle `users`, et cette fois l'ordre est
inversé : on n'écrit rien tant qu'un test ne le réclame pas.

Votre mission, depuis le répertoire du projet :

1. Écrire les **assertions d'abord**, sur un rôle dont les tâches n'existent pas
   encore, et lancer le cycle pour les voir échouer. Un test qui n'a jamais
   échoué ne prouve rien.
2. Déclarer le contrat d'entrée du rôle avant son code : la forme et le type de
   la liste d'utilisateurs à créer, pour qu'un appel fautif soit rejeté d'entrée.
3. Écrire alors le **minimum** de tâches qui font passer les assertions au vert,
   en bouclant sur les utilisateurs demandés plutôt qu'en figeant le moindre nom.
4. Refactorer une fois au vert, en utilisant la suite comme filet : elle doit
   rester verte pendant la réécriture, sinon elle ne vous protégeait pas.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-tdd-cycle/

## 🎯 Challenge : un vrai cycle TDD avec Molecule

### ✅ Mission

Le rôle `users` est livré avec son **contrat** (`meta/argument_specs.yml`,
`defaults/main.yml`) et ses **données d'entrée** (`converge.yml` crée
alice avec /bin/zsh et wheel, bob, carol). Deux fichiers sont vides, et
c'est tout l'objet du lab : vous les écrivez **dans l'ordre du TDD**.

1. **RED** : écrivez `molecule/default/verify.yml`, les tests d'abord.
   Au moins 4 assertions `ansible.builtin.assert` qui spécifient le
   comportement attendu (voir les commentaires du squelette). Lancez
   `molecule converge && molecule verify` : verify doit être **rouge**
   (le rôle est vide, c'est normal et c'est le point de départ).
2. **GREEN** : écrivez `roles/users/tasks/main.yml`, le minimum qui fait
   passer vos tests : une boucle sur `users_to_create` avec le module
   `ansible.builtin.user`. Relancez `molecule verify` : **vert**.
3. **REFACTOR** : nettoyez (loop_control, labels...) en gardant le vert.

État attendu (c'est ce que pytest vérifie) :

| Élément | Attente |
| --- | --- |
| `verify.yml` | au moins 4 tâches `ansible.builtin.assert` avec `that:` et `fail_msg:`, couvrant alice (shell + groupe), bob et carol |
| `tasks/main.yml` | boucle (`loop:`) sur `users_to_create`, module `ansible.builtin.user`, fallback `users_default_shell`, `append: true` pour les groupes |
| `converge.yml` | inchangé : ce sont les données du contrat |
| Le tout | `molecule syntax` passe (pytest l'exécute réellement) |

### 🧩 Bloqué ?

```bash
dsoxlab hint molecule-tdd-cycle
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` la séquence réellement exécutée
(converge, verify rouge, implémentation, verify vert). Ce journal doit
exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/tdd-cycle/challenge/tests/
```

La preuve d'exécution complète (`molecule test`, nécessite Podman) est marquée
`slow` et se joue désormais **par défaut** avec la commande ci-dessus (environ
24 secondes, image en cache). En environnement contraint (sans Podman),
désélectionnez-la avec `-m 'not slow'` :

```bash
pytest -v -m 'not slow' labs/molecule/tdd-cycle/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-tdd-cycle
```

### 💡 Pour aller plus loin

- Ajoutez un utilisateur `dave` dans converge.yml : quels tests écrire
  d'abord ?
- `molecule idempotence` : le second run du rôle doit être changed=0.
- Comparez avec le verifier testinfra du lab 66.
