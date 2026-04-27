# Lab — Module `lineinfile:` (modifier une ligne dans un fichier)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Module lineinfile Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/)

`ansible.builtin.lineinfile:` modifie **une seule ligne** dans un fichier
existant : ajouter si absente, remplacer une ligne identifiée par regexp,
ou supprimer. C'est l'outil de base pour **éditer un fichier de
configuration** dont on contrôle juste quelques paramètres — `sshd_config`,
`sudoers`, `/etc/hosts`, `/etc/sysctl.conf`.

**Différence clé avec `blockinfile:`** : `lineinfile:` = 1 ligne, `blockinfile:` = bloc multi-lignes avec markers automatiques.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Ajouter** une ligne si absente, ne rien faire si présente (idempotent).
2. **Remplacer** une ligne identifiée par regexp.
3. **Supprimer** une ligne par `state: absent`.
4. **Valider** la syntaxe avant écriture (`validate: "sshd -t -f %s"`).
5. **Préserver** une partie de la ligne via `backrefs: true`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak"
```

## 📚 Exercice 1 — Ajouter une ligne idempotente

Créez `lab.yml` :

```yaml
---
- name: Demo lineinfile — ajout simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Activer le forwarding IPv4
      ansible.builtin.lineinfile:
        path: /etc/sysctl.conf
        line: "net.ipv4.ip_forward=1"
        state: present
```

Lancez 2 fois et observez :

```bash
ansible-playbook labs/modules-fichiers/lineinfile/lab.yml
ansible-playbook labs/modules-fichiers/lineinfile/lab.yml   # → 2e run = ok (idempotent)
```

## 📚 Exercice 2 — Remplacer via regexp + validate

```yaml
- name: Désactiver le login root SSH
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^\s*#?\s*PermitRootLogin\s'
    line: "PermitRootLogin no"
    state: present
    validate: "sshd -t -f %s"
  notify: Restart sshd
```

**À tester** : modifier la regexp pour qu'elle ne matche plus, vérifier que la
ligne s'ajoute à la fin du fichier au lieu de remplacer.

## 📚 Exercice 3 — Backrefs

```yaml
- name: Réduire MaxAuthTries SSH en gardant le format
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^(\s*MaxAuthTries\s+).*$'
    line: '\g<1>3'
    backrefs: true
    validate: "sshd -t -f %s"
```

**Observer** : avec `backrefs: true`, si la regexp ne matche pas, la ligne
n'est **PAS ajoutée** (différence cruciale).

## 🔍 Observations à noter

- **Idempotence** : un second run du playbook doit afficher `changed=0` sur
  toutes les tâches du module `ansible.builtin.lineinfile`. Si une tâche reste `changed=1`, c'est
  que la regex/condition n'est pas ancrée correctement (cf. exercices).
- **FQCN explicite** : `ansible.builtin.lineinfile` (et non son nom court) — `ansible-lint
  --profile production` le vérifie.
- **`validate:`** quand c'est disponible (lineinfile, copy, template) : un
  binaire externe contrôle la syntaxe du fichier avant écriture, ce qui évite
  de casser un service avec une config invalide.
- **Convention de ciblage** : ce lab cible **db1.lab** (un seul host pour
  isoler l'impact destructif).

## 🤔 Questions de réflexion

1. Quand utiliser `ansible.builtin.lineinfile` plutôt que `replace:` (regex multi-occurrences) ou `template:` (fichier complet généré) ? Listez 2 cas où chaque
   alternative serait préférable (lisibilité, idempotence, performance).

2. Si vous deviez modifier ligne à ligne dans des fichiers de config sur **50 serveurs en parallèle**, quels
   paramètres Ansible (`forks`, `serial`, `strategy`) ajusteriez-vous pour
   tenir un SLA de 5 minutes ?

3. Comment gérer le cas où le module échoue **partiellement** (succès sur
   certaines tâches, échec sur d'autres) ? Quelles stratégies permettent de
   reprendre sans tout rejouer (`block/rescue`, `--start-at-task`, marqueur
   d'état) ?

## 🚀 Challenge final

Une fois les exercices ci-dessus digérés, lancez le **challenge autonome** :

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-fichiers/lineinfile --challenge
# ou
cat labs/modules-fichiers/lineinfile/challenge/README.md
```

Le challenge demande d'écrire votre `challenge/solution.yml` sans regarder
les exercices. Validation par `pytest` :

```bash
pytest -v labs/modules-fichiers/lineinfile/challenge/tests/
```

## 💡 Pour aller plus loin

- Combinez `ansible.builtin.lineinfile` avec **`backup: true`** pour conserver une copie
  horodatée du fichier original avant modification — utile pour rollback.
- Étudiez **`check_mode: true`** + `--diff` : Ansible vous montre ce qu'il
  ferait sans rien appliquer. Indispensable en production.
- Comparez la **performance** entre 1 tâche `ansible.builtin.lineinfile` × 10 et 1 tâche
  `template:` qui génère le fichier complet en une fois — souvent le
  template est plus rapide ET plus lisible quand le nombre de modifs grossit.

## 🧹 Cleanup

```bash
make clean
```

Ou manuellement :

```bash
ansible db1.lab -b -m shell -a "cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config && systemctl restart sshd"
```

## 📂 Solution

Voir `solution/modules-fichiers/lineinfile/solution.yml`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-fichiers/lineinfile/lab.yml
ansible-lint labs/modules-fichiers/lineinfile/challenge/solution.yml
ansible-lint --profile production labs/modules-fichiers/lineinfile/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques RHCE 2026.

