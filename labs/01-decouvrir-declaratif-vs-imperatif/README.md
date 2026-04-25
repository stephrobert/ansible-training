# Déclaratif vs impératif — Pourquoi Ansible ne ressemble pas à Bash

Bienvenue dans ce premier lab pratique sur la philosophie d'Ansible ! 🚀

---

## 🧠 Rappel et lecture recommandée

🔗 [**Déclaratif vs impératif : la même tâche, deux philosophies**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/)

Cette page du blog explique :

- Le contraste entre un **script Bash impératif** (qui dérive à chaque relance) et un **playbook Ansible déclaratif** (qui converge vers un état désiré)
- La notion d'**idempotence** et son signal `changed=0` au second passage
- Les **modules idempotents** (`dnf`, `template`, `lineinfile`) vs **non-idempotents** (`shell`, `command`)
- Pourquoi `creates:` / `removes:` rendent un module shell idempotent

---

## 🌟 Objectif du TP

À la fin de ce TP, vous aurez **vu de vos yeux** :

1. Un script Bash naïf qui **dérive** à chaque exécution sur la même cible
2. Le même objectif (déployer nginx) écrit en **playbook Ansible idempotent**
3. La preuve mécanique : second run du playbook → `changed=0`, le script Bash → toujours `changed`

C'est le **déclic mental** : sans cette différence comprise, vous écrivez du Bash en YAML et vous passez à côté de l'apport d'Ansible.

---

## ⚙️ Arborescence du lab

```text
labs/01-decouvrir-declaratif-vs-imperatif/
├── README.md           ← ce fichier
├── Makefile            ← orchestration setup / run-bash / run-ansible / verify / clean
├── playbook.yml        ← équivalent déclaratif Ansible
├── scripts/
│   └── install-nginx-impératif.sh   ← script Bash naïf
└── challenge/
    └── tests/
        └── test_idempotence.py       ← pytest+testinfra qui valide la convergence
```

---

## ⚙️ Exercices pratiques

### Exercice 1 — Voir le script Bash dériver

Depuis la racine du repo, lancez **3 fois** le script Bash via Make :

```bash
cd labs/01-decouvrir-declaratif-vs-imperatif
make run-bash
```

Le script :

1. Installe nginx (idempotent côté `dnf`, mais le script ne le sait pas)
2. **Ajoute** une ligne `Servi par <hostname>` à `index.html` à chaque appel
3. Démarre nginx

Résultat : `index.html` contient **1 ligne** au 1er run, **2** au 2e, **3** au 3e — c'est la dérive du modèle impératif.

### Exercice 2 — Voir le playbook Ansible converger

Réinitialisez l'état et lancez **3 fois** le playbook équivalent :

```bash
make setup        # remet l'état initial
make run-ansible
```

Résultat : `index.html` contient **toujours 1 ligne**. Le playbook a vérifié l'état avant d'agir, et a **convergé** vers le résultat souhaité — peu importe combien de fois on le relance.

### Exercice 3 — Vérifier l'idempotence par les tests

```bash
make verify
```

Lance la suite `pytest+testinfra` qui :

- Vérifie que `nginx` est installé et running sur web1
- Vérifie qu'`index.html` contient **exactement une ligne** `Servi par ...`
- Relance le playbook une fois de plus et vérifie que la sortie contient `changed=0` (preuve d'idempotence stricte)

### Exercice 4 — Nettoyer

```bash
make clean
```

Désinstalle nginx, retire la règle firewalld, supprime `index.html`. Le lab est prêt à être rejoué from scratch.

---

## 🚀 Pour aller plus loin

- Modifiez le script Bash pour le rendre **idempotent** : ajoutez un test sur la présence de la ligne avant de l'écrire (`grep -q "Servi par" || echo "..."`). Vérifiez que le 3e run ne dérive plus.
- Modifiez le playbook pour utiliser `lineinfile` (idempotent par regex) au lieu de `copy` (idempotent par checksum). Comparez les comportements.
- Ajoutez **`creates: /var/lib/nginx-installed.flag`** sur une fausse tâche `shell:` puis observez le `skipped` au second run.

---

## 🧪 Validation en CI

Tous les `make verify` du repo doivent passer. Pour l'audit complet :

```bash
make test-all
```

Bonne pratique ! 🧠
