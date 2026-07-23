# 🎯 Challenge : écrire votre premier scénario Molecule

## ✅ Mission

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

## 🧩 Bloqué ?

```bash
dsoxlab hint molecule-introduction
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 📓 Journal de commandes

Quand votre scénario est prêt, consignez dans `challenge/solution.sh` les
commandes Molecule que vous avez exécutées. Ce journal doit exister pour
que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/introduction/challenge/tests/
```

Le test charge vos trois fichiers YAML, contrôle leur sémantique, puis
lance réellement `molecule syntax`.

## 🧹 Reset

```bash
dsoxlab clean molecule-introduction
```

## 💡 Pour aller plus loin

- Lab 63 : enrichir la config (prepare.yml, requirements.yml, test_sequence).
- Lab 64 : cycle TDD complet sur un nouveau rôle.
- Lab 65 : multi-distro (RHEL + Debian + Ubuntu).
