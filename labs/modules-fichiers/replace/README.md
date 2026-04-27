# Lab — Module `replace:` (remplacer un motif dans un fichier)

> 💡 **Lab autonome.** Pré-requis : `ansible all -m ansible.builtin.ping` répond `pong`.

## 🧠 Rappel

🔗 [**Module replace Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/)

`ansible.builtin.replace:` substitue **toutes les occurrences** d'un motif
regex dans un fichier — sans toucher au reste de la ligne ni du fichier.
C'est l'outil pour les **changements transversaux** : mettre à jour une URL
d'API, changer un nom d'hôte, propager une nouvelle version.

**Différence clé avec `lineinfile:`** : `replace:` modifie un **motif partiel**
n'importe où dans le fichier ; `lineinfile:` modifie une **ligne entière**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Substituer** un motif partout dans un fichier.
2. **Limiter** la zone via `before:` et `after:`.
3. **Préserver** une partie du motif via groupes de capture.
4. **Distinguer** `replace:` de `lineinfile:` selon le besoin.
5. **Diagnostiquer** une idempotence cassée par double run.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m copy -a "dest=/etc/myapp.conf content='url=http://api-old.example.com/v1\nport=8080\n[server]\nssl_enabled=false\n[client]\nssl_enabled=false\n'"
```

## 📚 Exercice 1 — Substitution simple toutes occurrences

```yaml
---
- name: Demo replace
  hosts: db1.lab
  become: true
  tasks:
    - name: Forcer https sur les URL d'API
      ansible.builtin.replace:
        path: /etc/myapp.conf
        regexp: 'http://api-old\.example\.com'
        replace: 'https://api.example.com'
```

Lancez 2 fois et vérifiez l'idempotence (2e run = `ok`).

## 📚 Exercice 2 — Limiter avec before/after

```yaml
- name: Activer SSL UNIQUEMENT dans la section [server]
  ansible.builtin.replace:
    path: /etc/myapp.conf
    after: '\[server\]'
    before: '\[client\]'
    regexp: 'ssl_enabled\s*=\s*false'
    replace: 'ssl_enabled = true'
```

**Vérifier** : `ssl_enabled` reste `false` dans la section `[client]`.

> ⚠️ **Piège validé en lab** : avec `before:` et `after:`, l'ancrage `^` ne
> propage **pas** le mode MULTILINE Python. Si vous écrivez
> `regexp: '^ssl_enabled...'` avec before/after, la regexp matche **uniquement
> le tout début** de la zone extraite (pas chaque ligne) et la substitution
> échoue silencieusement. **Solution** : retirer le `^` quand on combine avec
> before/after — le contexte de zone restreint suffit à éviter les faux
> matches dans d'autres sections.

## 📚 Exercice 3 — Pièges idempotence

Cassez volontairement l'idempotence pour comprendre :

```yaml
- ansible.builtin.replace:
    path: /etc/myapp.conf
    regexp: 'http'         # trop large
    replace: 'https://http' # contient toujours 'http' → idempotence cassée
```

Lancez 2 fois → la 2e run = `changed` aussi. Comprenez pourquoi.

## 🔍 Observations à noter

- **Idempotence** : un second run du playbook doit afficher `changed=0` sur
  toutes les tâches du module `ansible.builtin.replace`. Si une tâche reste `changed=1`, c'est
  que la regex/condition n'est pas ancrée correctement (cf. exercices).
- **FQCN explicite** : `ansible.builtin.replace` (et non son nom court) — `ansible-lint
  --profile production` le vérifie.
- **`validate:`** quand c'est disponible (lineinfile, copy, template) : un
  binaire externe contrôle la syntaxe du fichier avant écriture, ce qui évite
  de casser un service avec une config invalide.
- **Convention de ciblage** : ce lab cible **db1.lab** (un seul host pour
  isoler l'impact destructif).

## 🤔 Questions de réflexion

1. Quand utiliser `ansible.builtin.replace` plutôt que `lineinfile:` (1 ligne unique) ou `blockinfile:` (bloc délimité) ? Listez 2 cas où chaque
   alternative serait préférable (lisibilité, idempotence, performance).

2. Si vous deviez substituer un motif partout dans un fichier sur **50 serveurs en parallèle**, quels
   paramètres Ansible (`forks`, `serial`, `strategy`) ajusteriez-vous pour
   tenir un SLA de 5 minutes ?

3. Comment gérer le cas où le module échoue **partiellement** (succès sur
   certaines tâches, échec sur d'autres) ? Quelles stratégies permettent de
   reprendre sans tout rejouer (`block/rescue`, `--start-at-task`, marqueur
   d'état) ?

## 🚀 Challenge final

Une fois les exercices ci-dessus digérés, lancez le **challenge autonome** :

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-fichiers/replace --challenge
# ou
cat labs/modules-fichiers/replace/challenge/README.md
```

Le challenge demande d'écrire votre `challenge/solution.yml` sans regarder
les exercices. Validation par `pytest` :

```bash
pytest -v labs/modules-fichiers/replace/challenge/tests/
```

## 💡 Pour aller plus loin

- Combinez `ansible.builtin.replace` avec **`backup: true`** pour conserver une copie
  horodatée du fichier original avant modification — utile pour rollback.
- Étudiez **`check_mode: true`** + `--diff` : Ansible vous montre ce qu'il
  ferait sans rien appliquer. Indispensable en production.
- Comparez la **performance** entre 1 tâche `ansible.builtin.replace` × 10 et 1 tâche
  `template:` qui génère le fichier complet en une fois — souvent le
  template est plus rapide ET plus lisible quand le nombre de modifs grossit.

## 🧹 Cleanup

```bash
make clean
```

## 📂 Solution

Voir `solution/modules-fichiers/replace/solution.yml`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-fichiers/replace/lab.yml
ansible-lint labs/modules-fichiers/replace/challenge/solution.yml
ansible-lint --profile production labs/modules-fichiers/replace/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques RHCE 2026.

