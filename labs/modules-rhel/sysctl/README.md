# Lab 46 — Module `sysctl:` (paramètres kernel)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Module sysctl Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/rhel-systeme/module-sysctl/)

`ansible.posix.sysctl:` gère les **paramètres kernel** runtime via `sysctl`
(fichier `/etc/sysctl.conf` ou `/etc/sysctl.d/*.conf`). Cas d'usage RHCE
2026 typiques : activer **IP forwarding**, ajuster les **buffers réseau**,
durcir les paramètres de sécurité (`kernel.kptr_restrict`,
`net.ipv4.tcp_syncookies`).

Module de la collection **`ansible.posix`**. Options critiques : **`name:`**,
**`value:`**, **`state:`**, **`sysctl_file:`** (chemin custom dans
`/etc/sysctl.d/`), **`reload:`** (applique maintenant).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Modifier** un paramètre kernel avec persistance et application immédiate.
2. **Choisir** entre `/etc/sysctl.conf` (legacy) et `/etc/sysctl.d/<file>.conf`
   (modulaire).
3. **Distinguer** une modification **runtime** (sysctl -w) d'une modification
   **persistée**.
4. **Vérifier** le paramètre courant via `command: sysctl -n` ou
   `register: + reload:`.
5. **Diagnostiquer** un paramètre qui revient à sa valeur après reboot.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/sysctl.d/99-rhce-lab.conf; sysctl -p; true"
```

## 📚 Exercice 1 — Paramètre dans `/etc/sysctl.conf` (le défaut)

```yaml
---
- name: Demo sysctl
  hosts: db1.lab
  become: true
  tasks:
    - name: Activer l IP forwarding (persistant)
      ansible.posix.sysctl:
        name: net.ipv4.ip_forward
        value: '1'
        state: present
        reload: true

    - name: Verifier la valeur courante
      ansible.builtin.command: sysctl -n net.ipv4.ip_forward
      register: ip_fwd
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        msg: "ip_forward = {{ ip_fwd.stdout }}"
```

**Lancez** :

```bash
ansible-playbook labs/modules-rhel/sysctl/lab.yml
```

🔍 **Observation** :

- Le module modifie `/etc/sysctl.conf` (par défaut) ou crée la ligne si absente.
- **`reload: true`** lance `sysctl -p` qui applique immédiatement les valeurs.
- 2e run → `changed=0` (idempotent).

**Vérifier la persistance** :

```bash
ssh ansible@db1.lab 'grep net.ipv4.ip_forward /etc/sysctl.conf /etc/sysctl.d/* 2>/dev/null'
```

## 📚 Exercice 2 — `sysctl_file:` pour modulariser

Plutôt que tout entasser dans `/etc/sysctl.conf`, mieux vaut **un fichier par
rôle** dans `/etc/sysctl.d/`.

```yaml
- name: Tuning reseau dans /etc/sysctl.d/99-rhce-lab.conf
  ansible.posix.sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    sysctl_file: /etc/sysctl.d/99-rhce-lab.conf
    reload: true
  loop:
    - { name: net.core.somaxconn, value: '4096' }
    - { name: net.ipv4.tcp_max_syn_backlog, value: '8192' }
    - { name: net.ipv4.tcp_syncookies, value: '1' }
```

🔍 **Observation** : un seul fichier `/etc/sysctl.d/99-rhce-lab.conf` contient
les 3 paramètres. **Avantages** :

- **Versionné** dans le repo Ansible (`fetch:` pour audit).
- **Supprimable proprement** : `state: absent` retire la ligne.
- **Préfixe numérique** (`99-`) contrôle l'ordre de chargement (cf. doc
  systemd-sysctl(8) : ordre alphabétique).

## 📚 Exercice 3 — Le piège : `reload: false`

```yaml
- name: Modifier sans reload
  ansible.posix.sysctl:
    name: vm.swappiness
    value: '10'
    state: present
    reload: false   # Defaut : false !
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sysctl -n vm.swappiness'
# → 60 (l ancienne valeur, pas 10 !)

ssh ansible@db1.lab 'cat /etc/sysctl.conf | grep swappiness'
# → vm.swappiness = 10 (modifie en persistant)
```

🔍 **Observation** : sans `reload: true`, le paramètre est modifié dans le
fichier **mais pas appliqué** au runtime — il faudra un `sysctl -p` manuel
ou un reboot pour prendre effet.

**Règle** : **toujours** `reload: true` si vous voulez l'effet immédiat.
Exception : si vous avez plusieurs `sysctl:` consécutifs, mettre `reload:
false` partout SAUF sur la dernière (économie de N-1 reload).

## 📚 Exercice 4 — Suppression d'un paramètre

```yaml
- name: Retirer le tuning si plus necessaire
  ansible.posix.sysctl:
    name: net.core.somaxconn
    state: absent
    sysctl_file: /etc/sysctl.d/99-rhce-lab.conf
    reload: true
```

🔍 **Observation** : `state: absent` retire la ligne du fichier. Si le paramètre
était surchargé via plusieurs fichiers (par exemple aussi dans
`/etc/sysctl.conf`), le **deuxième** prend le relais — toujours auditer après
suppression.

**Vérifier la valeur effective** :

```yaml
- ansible.builtin.command: sysctl -n net.core.somaxconn
  register: somaxconn
  changed_when: false

- ansible.builtin.debug:
    msg: "Valeur courante : {{ somaxconn.stdout }}"
    # → Sera la valeur kernel par defaut (4096 sur RHEL 10)
```

## 📚 Exercice 5 — Pattern durcissement CIS

Le CIS Benchmark RHEL impose une dizaine de paramètres `sysctl` pour le
durcissement.

```yaml
- name: Durcissement CIS (sysctl)
  ansible.posix.sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    sysctl_file: /etc/sysctl.d/99-cis-hardening.conf
    reload: true
  loop:
    # Reseau
    - { name: net.ipv4.conf.all.send_redirects, value: '0' }
    - { name: net.ipv4.conf.default.send_redirects, value: '0' }
    - { name: net.ipv4.conf.all.accept_redirects, value: '0' }
    - { name: net.ipv4.conf.all.accept_source_route, value: '0' }
    - { name: net.ipv4.tcp_syncookies, value: '1' }

    # Securite kernel
    - { name: kernel.kptr_restrict, value: '2' }
    - { name: kernel.dmesg_restrict, value: '1' }
    - { name: kernel.randomize_va_space, value: '2' }

    # FS
    - { name: fs.suid_dumpable, value: '0' }
```

🔍 **Observation** : pattern **liste de dicts** + `loop:` rend le code propre
et auditable (un fichier dédié, paramètres groupés, modifiable sans toucher au
playbook).

## 📚 Exercice 6 — Le piège : paramètres avec `.` ou `/`

Certains paramètres incluent des **noms d'interface** :

```yaml
# Pour eth0
- ansible.posix.sysctl:
    name: net.ipv4.conf.eth0.forwarding
    value: '1'
```

Sur RHEL 10, les interfaces s'appellent souvent `enp0s3`, `ens18`, etc. — le
nom doit **matcher exactement** ce que `ip a` renvoie.

**Pattern défensif** :

```yaml
- name: Activer forwarding sur l interface principale
  ansible.posix.sysctl:
    name: "net.ipv4.conf.{{ ansible_default_ipv4.interface }}.forwarding"
    value: '1'
    state: present
    reload: true
```

`ansible_default_ipv4.interface` est le **fact** qui donne le nom de
l'interface principale — fonctionne sur n'importe quelle distro.

## 🔍 Observations à noter

- **`ansible.posix.sysctl:`** = paramètres kernel persistés.
- **`reload: true`** pour appliquer immédiatement (sinon ça reste en fichier).
- **`sysctl_file: /etc/sysctl.d/<name>.conf`** = pattern modulaire préféré.
- **`state: absent`** retire la ligne (mais d'autres fichiers peuvent reprendre la main).
- **Préfixe numérique** dans `sysctl.d/` contrôle l'ordre (`99-` = appliqué dernier).
- **Pattern CIS** : un fichier dédié `/etc/sysctl.d/99-cis-hardening.conf`.

## 🤔 Questions de réflexion

1. Vous voulez **annuler** un paramètre `sysctl` posé par le système (defaults
   RHEL). Suffit-il de `state: absent` ? Pourquoi le paramètre peut "revenir" ?

2. Vous avez 10 paramètres à modifier en une passe. Quel est l'**impact
   performance** de `reload: true` sur chacun vs `reload: true` sur le dernier
   uniquement ?

3. Un paramètre `sysctl` est modifié à plusieurs endroits
   (`/etc/sysctl.conf`, `/etc/sysctl.d/99-app.conf`, `/etc/sysctl.d/99-cis.conf`).
   Lequel **gagne** au boot ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`reload_required:`** : sur certains paramètres (`kernel.hostname`,
  `kernel.modules_disabled`), le `reload` ne suffit pas — il faut un reboot.
  Le module l'indique en sortie.
- **Module `community.general.modprobe:`** : charger un module kernel
  (`ip_vs`, `nf_conntrack`) — souvent prérequis pour des paramètres `sysctl`
  spécifiques.
- **`/run/sysctl.d/` vs `/etc/sysctl.d/`** : `/run/` est volatile (perdu au
  reboot). Pour des configs **transitoires** (containers).
- **Pattern `sysctl_set: true`** : option qui **vérifie** que le paramètre est
  vraiment **lisible** par sysctl avant d'écrire dans le fichier. Sécurité
  contre les typos.
- **Lab 44 (firewalld)** + **45 (selinux)** + **46 (sysctl)** = la trinité du
  durcissement RHEL.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-rhel/sysctl/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-rhel/sysctl/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-rhel/sysctl/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
