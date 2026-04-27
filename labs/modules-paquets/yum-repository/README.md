# Lab — Module `yum_repository:` (déclarer un dépôt RPM)

> 💡 **Lab autonome.** Pré-requis : VM RHEL/AlmaLinux/Rocky disponible et `ansible-galaxy collection install ansible.posix`.

## 🧠 Rappel

🔗 [**Module yum_repository Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/)

`ansible.builtin.yum_repository:` déclare un **dépôt RPM** (yum/dnf) en
générant le fichier `.repo` dans `/etc/yum.repos.d/`. C'est l'outil pour
**activer EPEL**, ajouter le dépôt **Docker CE**, déclarer un **dépôt
interne**, ou désactiver un dépôt par défaut.

**Chaîne typique** : `rpm_key:` (importe la clé GPG) →
`yum_repository:` (déclare le dépôt) → `dnf:` (installe les paquets).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Importer** une clé GPG avec `rpm_key:`.
2. **Déclarer** un dépôt avec `yum_repository:` (gpgcheck mandatory).
3. **Désactiver** un dépôt sans le supprimer (`enabled: false`).
4. **Distinguer** `yum_repository:` (déclare un dépôt) de `dnf:` (installe).
5. Comprendre les **macros** `$releasever`, `$basearch`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping        # supposer une VM AlmaLinux/Rocky
```

## 📚 Exercice 1 — Activer EPEL 9

```yaml
---
- name: Activer EPEL 9
  hosts: db1.lab    # idéalement une VM AlmaLinux 9 ou Rocky 9
  become: true
  tasks:
    - name: Importer la clé GPG EPEL 9
      ansible.builtin.rpm_key:
        state: present
        key: https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9

    - name: Déclarer le dépôt EPEL 9
      ansible.builtin.yum_repository:
        name: epel
        description: "Extra Packages for Enterprise Linux 9"
        baseurl: "https://dl.fedoraproject.org/pub/epel/9/Everything/$basearch/"
        gpgcheck: true
        gpgkey: https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9
        enabled: true
        state: present

    - name: Tester — installer un paquet d'EPEL
      ansible.builtin.dnf:
        name: htop
        state: present
```

Lancez 2 fois — 2e run `ok` (idempotent).

## 📚 Exercice 2 — Désactiver un dépôt sans le supprimer

```yaml
- name: Désactiver le dépôt epel sans supprimer le fichier
  ansible.builtin.yum_repository:
    name: epel
    description: "EPEL — désactivé par stratégie"
    file: epel
    enabled: false
    state: present
```

**Vérifier** : `dnf repolist all | grep epel` montre `disabled`.

## 📚 Exercice 3 — Dépôt local sans GPG (pour test, JAMAIS en prod)

```yaml
- ansible.builtin.yum_repository:
    name: local-test
    description: "Dépôt local de test"
    baseurl: "file:///srv/repo/"
    gpgcheck: false   # uniquement en lab
```

**Lire la doc sur la sécurité** — `gpgcheck: false` est une faille en production.

## 🔍 Observations à noter

- **Idempotence** : un second run du playbook doit afficher `changed=0` sur
  toutes les tâches du module `ansible.builtin.yum_repository`. Si une tâche reste `changed=1`, c'est
  que la regex/condition n'est pas ancrée correctement (cf. exercices).
- **FQCN explicite** : `ansible.builtin.yum_repository` (et non son nom court) — `ansible-lint
  --profile production` le vérifie.
- **`validate:`** quand c'est disponible (lineinfile, copy, template) : un
  binaire externe contrôle la syntaxe du fichier avant écriture, ce qui évite
  de casser un service avec une config invalide.
- **Convention de ciblage** : ce lab cible **db1.lab** (un seul host pour
  isoler l'impact destructif).

## 🤔 Questions de réflexion

1. Quand utiliser `ansible.builtin.yum_repository` plutôt que manipulation manuelle de `/etc/yum.repos.d/*.repo` via `copy:` (moins idempotent) ? Listez 2 cas où chaque
   alternative serait préférable (lisibilité, idempotence, performance).

2. Si vous deviez déclarer ou désactiver un dépôt RPM sur **50 serveurs en parallèle**, quels
   paramètres Ansible (`forks`, `serial`, `strategy`) ajusteriez-vous pour
   tenir un SLA de 5 minutes ?

3. Comment gérer le cas où le module échoue **partiellement** (succès sur
   certaines tâches, échec sur d'autres) ? Quelles stratégies permettent de
   reprendre sans tout rejouer (`block/rescue`, `--start-at-task`, marqueur
   d'état) ?

## 🚀 Challenge final

Une fois les exercices ci-dessus digérés, lancez le **challenge autonome** :

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-paquets/yum-repository --challenge
# ou
cat labs/modules-paquets/yum-repository/challenge/README.md
```

Le challenge demande d'écrire votre `challenge/solution.yml` sans regarder
les exercices. Validation par `pytest` :

```bash
pytest -v labs/modules-paquets/yum-repository/challenge/tests/
```

## 💡 Pour aller plus loin

- Combinez `ansible.builtin.yum_repository` avec **`backup: true`** pour conserver une copie
  horodatée du fichier original avant modification — utile pour rollback.
- Étudiez **`check_mode: true`** + `--diff` : Ansible vous montre ce qu'il
  ferait sans rien appliquer. Indispensable en production.
- Comparez la **performance** entre 1 tâche `ansible.builtin.yum_repository` × 10 et 1 tâche
  `template:` qui génère le fichier complet en une fois — souvent le
  template est plus rapide ET plus lisible quand le nombre de modifs grossit.

## 🧹 Cleanup

```bash
make clean
```

## 📂 Solution

Voir `solution/modules-paquets/yum-repository/solution.yml`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-paquets/yum-repository/lab.yml
ansible-lint labs/modules-paquets/yum-repository/challenge/solution.yml
ansible-lint --profile production labs/modules-paquets/yum-repository/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques RHCE 2026.

