# Lab 44 — Module `firewalld:` (gérer le pare-feu RHEL)

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

🔗 [**Module firewalld Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/rhel-systeme/module-firewalld/)

`ansible.posix.firewalld:` gère **firewalld**, le pare-feu par défaut sur RHEL 7+,
AlmaLinux, RockyLinux. C'est le module n°1 RHCE 2026 pour ouvrir/fermer des
**ports**, autoriser des **services** prédéfinis (http, https, ssh), gérer les
**zones** (`public`, `internal`, `dmz`).

Module de la collection **`ansible.posix`** (pas builtin) — `ansible-galaxy
collection install ansible.posix`.

Options critiques : **`service:`** (nom de service prédéfini) ou **`port:`**
(format `8080/tcp`), **`state:`** (`enabled` / `disabled`), **`permanent: true`**
+ **`immediate: true`** (sinon piège classique), **`zone:`**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Autoriser** un service prédéfini (http, https, ssh) avec `service:`.
2. **Ouvrir** un port custom avec `port:` (format `8080/tcp`).
3. **Comprendre** le piège **`permanent: true` + `immediate: true`** (et pourquoi
   les deux).
4. **Distinguer** les **zones** firewalld (`public`, `internal`, `dmz`).
5. **Recharger** firewalld via `systemd_service:` quand nécessaire.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install ansible.posix
ansible web1.lab -m ping
ansible web1.lab -b -m systemd_service -a "name=firewalld state=started enabled=true"
ansible web1.lab -b -m shell -a "firewall-cmd --remove-port=8080/tcp 2>/dev/null; firewall-cmd --remove-port=8443/tcp 2>/dev/null; firewall-cmd --remove-service=https 2>/dev/null; firewall-cmd --runtime-to-permanent; true"
```

## 📚 Exercice 1 — Le piège `permanent` vs `immediate`

`firewalld` distingue **deux états** :

- **runtime** : règles actives **maintenant** (perdues au reboot).
- **permanent** : règles persistées dans `/etc/firewalld/`, **chargées au reboot**.

Sans `permanent:`, vous ouvrez maintenant mais perdez au reboot. Sans
`immediate:` (avec `permanent: true`), vous persistez mais **rien n'est appliqué
maintenant**.

```yaml
# ❌ Piege : ouvre maintenant, perd au reboot
- ansible.posix.firewalld:
    service: http
    state: enabled
    # Pas de permanent → runtime only

# ❌ Piege : persiste mais pas applique maintenant
- ansible.posix.firewalld:
    service: http
    state: enabled
    permanent: true
    # Pas de immediate → reload necessaire pour appliquer

# ✅ Bon : applique maintenant ET persiste
- ansible.posix.firewalld:
    service: http
    state: enabled
    permanent: true
    immediate: true
```

**Règle absolue** : **toujours** mettre `permanent: true` + `immediate: true`.

## 📚 Exercice 2 — Autoriser un service prédéfini

Créez `lab.yml` :

```yaml
---
- name: Demo firewalld
  hosts: web1.lab
  become: true
  tasks:
    - name: Autoriser HTTP (service predefini)
      ansible.posix.firewalld:
        service: http
        state: enabled
        permanent: true
        immediate: true

    - name: Autoriser HTTPS
      ansible.posix.firewalld:
        service: https
        state: enabled
        permanent: true
        immediate: true

    - name: Lister les services autorises
      ansible.builtin.command: firewall-cmd --list-services
      register: fw_services
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        var: fw_services.stdout
        # → "ssh dhcpv6-client cockpit http https"
```

**Lancez** :

```bash
ansible-playbook labs/modules-rhel/firewalld/lab.yml
```

🔍 **Observation** : `http` et `https` sont ajoutés à la liste des services
autorisés. **Idempotence** : 2e run → `changed=0`.

`firewall-cmd --get-services` liste tous les services prédéfinis disponibles
(plus de 100). Préférer un service à un port quand possible — l'intent est
plus clair (`http` plutôt que `80/tcp`).

## 📚 Exercice 3 — Ouvrir un port custom

```yaml
- name: Ouvrir le port 8080/tcp (app custom)
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true

- name: Ouvrir le port 8443/tcp (HTTPS custom)
  ansible.posix.firewalld:
    port: 8443/tcp
    state: enabled
    permanent: true
    immediate: true
```

**Format** : `<port>/<protocol>` — `tcp`, `udp`. Pour des plages : `8000-8100/tcp`.

**Quand utiliser `port:` plutôt que `service:`** :

- App custom sans service prédéfini.
- Port non standard (8080 au lieu de 80).
- Stack interne avec ports privés (Prometheus 9090, Grafana 3000, etc.).

## 📚 Exercice 4 — Zones firewalld

```yaml
- name: Autoriser SSH dans la zone internal uniquement
  ansible.posix.firewalld:
    service: ssh
    zone: internal
    state: enabled
    permanent: true
    immediate: true

- name: Bloquer SSH dans la zone public
  ansible.posix.firewalld:
    service: ssh
    zone: public
    state: disabled
    permanent: true
    immediate: true
```

🔍 **Observation** : firewalld permet de **segmenter** les règles par zone.
Cas d'usage : un serveur multi-interfaces (eth0 public, eth1 internal) avec
des règles différentes par interface.

**Zones par défaut** sur RHEL : `public` (la plupart du trafic), `internal`,
`trusted`, `dmz`, `block`, `drop`.

`firewall-cmd --get-default-zone` montre la zone par défaut. La changer :

```yaml
- name: Changer la zone par defaut
  ansible.builtin.command: firewall-cmd --set-default-zone=internal
  changed_when: true
```

## 📚 Exercice 5 — Suppression d'une règle

```yaml
- name: Retirer le port 8080
  ansible.posix.firewalld:
    port: 8080/tcp
    state: disabled
    permanent: true
    immediate: true
```

Pas de `state: absent` pour firewalld — c'est `state: disabled`. La règle est
retirée des fichiers permanents et des règles runtime.

## 📚 Exercice 6 — Pattern complet : web stack

```yaml
- name: Stack web complete
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer httpd
      ansible.builtin.dnf:
        name: httpd
        state: present

    - name: Demarrer httpd
      ansible.builtin.systemd_service:
        name: httpd
        state: started
        enabled: true

    - name: Ouvrir HTTP et HTTPS
      ansible.posix.firewalld:
        service: "{{ item }}"
        state: enabled
        permanent: true
        immediate: true
      loop: [http, https]
```

🔍 **Observation** : `loop:` sur le service permet d'ouvrir plusieurs ports en
une tâche. **Ordre** : installer → démarrer → ouvrir le pare-feu (sinon le
service serait inaccessible le temps de la config).

## 📚 Exercice 7 — Le piège : firewalld désactivé

Si firewalld n'est **pas démarré**, le module **failed** :

```yaml
- name: Tenter d ouvrir un port
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true
```

Erreur : `firewalld is not running`.

**Solution** : démarrer firewalld d'abord :

```yaml
- name: S assurer que firewalld tourne
  ansible.builtin.systemd_service:
    name: firewalld
    state: started
    enabled: true

- name: Maintenant on peut ouvrir un port
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true
```

Sur des images Docker minimales ou des installs custom, firewalld peut être
absent ou remplacé par `iptables`/`nftables`. Le module assume firewalld.

## 🔍 Observations à noter

- **Module `ansible.posix.firewalld:`** (pas builtin — collection requise).
- **`permanent: true` + `immediate: true`** = règle d'or, toujours les deux.
- **`service:`** > **`port:`** quand un service prédéfini existe (lisibilité).
- **`zone:`** pour segmenter les règles par interface.
- **`state: disabled`** pour retirer (pas `absent`).
- **firewalld doit tourner** (`systemd_service:`) avant le module.

## 🤔 Questions de réflexion

1. Vous ouvrez le port 8080 avec **uniquement `permanent: true`**. Au prochain
   `firewall-cmd --list-ports`, le port apparaît-il ? Et après reboot ?

2. Vous avez 50 webservers et vous voulez **fermer SSH depuis l'internet**
   (zone `public`) tout en le **gardant ouvert depuis le LAN** (zone `internal`).
   Quel pattern ?

3. Pourquoi `firewalld` est-il préféré à `iptables` direct sur RHEL 8+ ?
   (indice : richesse des règles, persistance, rich-rules).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Rich rules** : règles avancées (limit-rate, log, masquerade) via
  `rich_rule:` parameter du module.
- **Service custom** : créer un service firewalld custom via `template:` sur
  `/etc/firewalld/services/<name>.xml`, puis `firewalld: service:` dessus.
- **`source:`** : autoriser uniquement depuis une IP ou un range
  (`source: 192.168.1.0/24` + `service: ssh`).
- **`masquerade: true`** : activer le NAT/SNAT (utile pour un router Linux ou
  une zone DMZ).
- **Lab 45 (selinux)** : compléter le pare-feu par les contextes SELinux pour
  une sécurité complète.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-rhel/firewalld/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-rhel/firewalld/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-rhel/firewalld/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
