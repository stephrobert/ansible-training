# Lab 38 — Module `systemd_service:` (gérer les services systemd)

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

🔗 [**Module systemd_service Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-systemd/)

Sur les distributions modernes (RHEL 7+, Ubuntu 16.04+), **tous les services**
sont gérés par **systemd**. Le module `ansible.builtin.systemd_service:`
(alias `systemd`) est plus puissant que le legacy `service:` :

- **Connaît `daemon_reload:`** (recharger systemd après modif d'un `.service`).
- **Distingue `state:`** (état immédiat) et **`enabled:`** (au boot) — deux
  options indépendantes.
- **Gère les unit files masqués** (`masked: true`).
- **Sait recharger sans redémarrer** (`state: reloaded`).

C'est le module n°1 pour les opérations services en RHCE 2026.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Distinguer** `state:` vs `enabled:` (état actuel vs boot).
2. **Recharger** un service sans coupure (`reloaded` vs `restarted`).
3. **Déposer un unit file custom** + `daemon_reload: true`.
4. **Masquer** un service dangereux (`masked: true`).
5. **Notifier** un service depuis un handler (pattern reload-on-change).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -f /etc/systemd/system/lab-marker.service /var/run/lab-marker.flag; systemctl daemon-reload"
```

## 📚 Exercice 1 — `state:` vs `enabled:` (deux options indépendantes)

Créez `lab.yml` :

```yaml
---
- name: Demo systemd state vs enabled
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer chrony
      ansible.builtin.dnf:
        name: chrony
        state: present

    - name: Demarrer MAINTENANT (mais pas au boot)
      ansible.builtin.systemd_service:
        name: chronyd
        state: started

    - name: Verifier le statut
      ansible.builtin.command: systemctl is-active chronyd
      register: chronyd_active
      changed_when: false

    - name: Verifier si enabled au boot
      ansible.builtin.command: systemctl is-enabled chronyd
      register: chronyd_enabled
      changed_when: false
      failed_when: false

    - name: Resume
      ansible.builtin.debug:
        msg: |
          active : {{ chronyd_active.stdout }}
          enabled : {{ chronyd_enabled.stdout }}
```

**Lancez** :

```bash
ansible-playbook labs/modules-services/systemd/lab.yml
```

🔍 **Observation** : le service est **active** (running maintenant) mais peut être
**disabled** (pas au boot) selon l'état initial. **`state:`** et **`enabled:`**
sont **indépendants**.

**Configuration normale** : les deux ensemble.

```yaml
- ansible.builtin.systemd_service:
    name: chronyd
    state: started
    enabled: true
```

## 📚 Exercice 2 — `reloaded` vs `restarted`

```yaml
- name: Modifier la conf chrony
  ansible.builtin.lineinfile:
    path: /etc/chrony.conf
    regexp: '^server '
    line: 'server 0.fr.pool.ntp.org iburst'

- name: Recharger SANS coupure
  ansible.builtin.systemd_service:
    name: chronyd
    state: reloaded

# Alternative : restarted (avec coupure)
- name: Redemarrer (coupure breve)
  ansible.builtin.systemd_service:
    name: chronyd
    state: restarted
```

| `state:` | Effet | Coupure |
|---|---|---|
| `restarted` | `systemctl restart` (stop + start) | Oui — brève (ms à secondes) |
| `reloaded` | `systemctl reload` (SIGHUP, recharge config) | Non — pas d'arrêt |

🔍 **Observation** : préférer **`reloaded`** quand le service le supporte (`nginx`,
`httpd`, `sshd`, `firewalld`, `chronyd`) — pas de coupure pour les clients connectés.

**`restarted`** reste nécessaire pour :

- Changement d'**unit file** (le binaire ou les arguments changent).
- Changement majeur que SIGHUP ne couvre pas.

## 📚 Exercice 3 — `daemon_reload:` après nouveau unit file

```yaml
- name: Deposer un unit file custom
  ansible.builtin.copy:
    content: |
      [Unit]
      Description=Lab Marker Service
      After=network.target

      [Service]
      Type=oneshot
      ExecStart=/bin/touch /var/run/lab-marker.flag
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/lab-marker.service
    mode: "0644"

- name: Recharger systemd ET activer le service
  ansible.builtin.systemd_service:
    name: lab-marker
    state: started
    enabled: true
    daemon_reload: true
```

🔍 **Observation** :

- **Sans `daemon_reload: true`**, systemd **ne voit pas** le nouveau unit file →
  `start` échouerait avec "unit not found".
- **Avec `daemon_reload: true`**, systemd recharge ses unit files **avant**
  d'agir sur le service.

**Quand l'utiliser** : **uniquement** quand vous **déposez ou modifiez** un unit
file. Pas besoin sur un `state: started` d'un service système standard.

**Vérifier le fonctionnement** :

```bash
ssh ansible@web1.lab 'systemctl status lab-marker && cat /var/run/lab-marker.flag'
```

## 📚 Exercice 4 — `masked: true` (interdire le start)

```yaml
- name: Masquer rpcbind (durcissement)
  ansible.builtin.systemd_service:
    name: rpcbind
    state: stopped
    enabled: false
    masked: true
```

🔍 **Observation** : **`masked: true`** lie l'unit file à `/dev/null` — toute
commande `systemctl start rpcbind` échoue silencieusement, **même par un humain**.
Pattern de **durcissement** absolu pour des services qu'on **interdit**.

**Différence avec `enabled: false`** :

- **`disabled`** = pas au boot, mais `systemctl start` manuel marche.
- **`masked`** = interdit toute forme de démarrage.

**Pour démasquer** :

```yaml
- ansible.builtin.systemd_service:
    name: rpcbind
    masked: false
    state: started
```

## 📚 Exercice 5 — Pattern handler (notification)

```yaml
- name: Modifier sshd_config
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
  notify: Reload sshd

# Plus loin dans le play (handlers section)
handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation** : le handler `Reload sshd` ne tourne que **si la tâche
`lineinfile:` a notifié** (=changement effectif), et **à la fin du play**.

**Avantages** :

- Pas de reload inutile si rien n'a changé.
- Reload en **fin de play** : si plusieurs tâches notifient le même handler,
  il tourne **une seule fois**.

Voir [Lab 06 - Handlers](../06-ecrire-code-handlers/) pour les détails.

## 📚 Exercice 6 — Boucle sur plusieurs services

```yaml
- name: Demarrer la stack monitoring
  ansible.builtin.systemd_service:
    name: "{{ item }}"
    state: started
    enabled: true
  loop:
    - chronyd
    - sshd
    - rsyslog
```

🔍 **Observation** : chaque itération est **une opération systemd indépendante**.
Pour 50 services, c'est lent — mais c'est rare d'avoir 50 services à démarrer
en parallèle.

**Pas de bénéfice à mettre `state: [...]`** : `name:` n'accepte qu'un service.

## 📚 Exercice 7 — Le piège : `[Install]` manquant

Si votre unit file custom n'a **pas de section `[Install]`**, `enabled: true`
**échoue silencieusement** — le service ne sera pas démarré au boot.

```ini
# ❌ Mauvais : pas de [Install]
[Unit]
Description=Mon service

[Service]
ExecStart=/usr/local/bin/myapp

# ✅ Bon : [Install] avec WantedBy
[Unit]
Description=Mon service

[Service]
ExecStart=/usr/local/bin/myapp

[Install]
WantedBy=multi-user.target
```

🔍 **Observation** : sans `[Install]`, `systemctl enable` retourne `Created
symlink ... → ...` mais **rien n'est créé dans `/etc/systemd/system/multi-user.target.wants/`**.
Au reboot, le service ne démarre pas.

**Toujours** vérifier qu'un unit file custom a `[Install] WantedBy=...`.

## 🔍 Observations à noter

- **`state:`** = état **immédiat** (started/stopped/restarted/reloaded).
- **`enabled:`** = démarrage **au boot** (indépendant de `state:`).
- **`reloaded`** > **`restarted`** quand le service le supporte — pas de coupure.
- **`daemon_reload: true`** est obligatoire **après** un nouveau unit file.
- **`masked: true`** = durcissement (interdit tout start, même manuel).
- **Section `[Install]`** dans l'unit file est obligatoire pour `enabled: true`.

## 🤔 Questions de réflexion

1. Vous modifiez `nginx.conf` via `template:`. Quelle option du module
   `systemd_service:` (avec `notify:` du `template:`) garantit zéro coupure pour
   les clients ?

2. Quelle est la différence entre `disabled` et `masked` au point de vue
   **opérateur humain** sur un serveur ? (indice : un opérateur peut-il toujours
   `systemctl start` ?)

3. Vous voulez créer 5 services personnalisés à partir d'un même template d'unit
   file. Quel pattern (combinaison `template`, `loop:`, `daemon_reload:`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`force: true`** : force l'action même si elle semble idempotente. Utile pour
  un `restarted` après détection externe d'un état dégradé.
- **Module `service:` (legacy)** : alternative pré-systemd, encore disponible.
  Utile uniquement sur des distros sans systemd (très rare aujourd'hui).
- **`scope: user`** : gérer les services **utilisateur** (`systemctl --user`).
  Avancé, peu utilisé en RHCE.
- **Pattern `socket activation`** : déposer un `.socket` + `.service` pour
  démarrer le service à la demande (pas en permanence).
- **Lab 39 (`cron:`)** : pour des **tâches planifiées** plutôt que des services
  long-living.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-services/systemd/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-services/systemd/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-services/systemd/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
