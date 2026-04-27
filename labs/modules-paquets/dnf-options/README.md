# Lab 37 — Module `dnf:` options spécifiques RHEL

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

🔗 [**Module dnf Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf/)

Sur un parc 100% RHEL/RockyLinux/AlmaLinux, **`dnf:` est plus puissant que
`package:`** parce qu'il expose les options **spécifiques de DNF** :

- **`enablerepo:`** / **`disablerepo:`** : activer / désactiver un repo le temps
  d'une opération.
- **`security: true`** / **`bugfix: true`** : limiter aux **errata** de sécurité
  ou de bugfix.
- **`exclude:`** : exclure des paquets (patterns wildcards).
- **`autoremove: true`** : nettoyer les dépendances orphelines.
- **`update_cache: true`** : forcer un refresh des métadonnées repos.
- **`download_only: true`** : pré-télécharger sans installer.

Ces options sont **explicites RHCE 2026** — vous serez testé sur le **patching
sécurité** (`security: true`) et l'activation temporaire de repos.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Activer un repo temporairement** avec `enablerepo:` (sans le persister).
2. **Patcher uniquement les CVE** avec `security: true`.
3. **Exclure le kernel** d'un upgrade massif (`exclude: kernel*`).
4. **Nettoyer** les dépendances orphelines avec `autoremove: true`.
5. **Pré-télécharger** des RPM avec `download_only: true` pour un upgrade
   air-gapped.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "dnf -y remove htop ncdu epel-release 2>/dev/null; true"
```

## 📚 Exercice 1 — `enablerepo: epel` (activer EPEL temporairement)

EPEL (Extra Packages for Enterprise Linux) contient `htop`, `ncdu`, `iftop`, etc.
qui ne sont pas dans les repos RHEL de base.

```yaml
---
- name: Demo dnf enablerepo
  hosts: db1.lab
  become: true
  tasks:
    - name: Installer epel-release (la conf du repo EPEL)
      ansible.builtin.dnf:
        name: epel-release
        state: present

    - name: Installer htop depuis EPEL (sans persister l activation)
      ansible.builtin.dnf:
        name: htop
        state: present
        enablerepo: epel

    - name: Verifier que htop est dispo
      ansible.builtin.command: htop --version
      register: htop_version
      changed_when: false

    - name: Afficher la version
      ansible.builtin.debug:
        msg: "{{ htop_version.stdout }}"
```

**Lancez** :

```bash
ansible-playbook labs/modules-paquets/dnf-options/lab.yml
```

🔍 **Observation** : `htop` est installé via EPEL. **`enablerepo:`** active EPEL
**uniquement pour cette tâche** — pas de modification persistante. Au prochain
`dnf list`, EPEL sera **désactivé** par défaut. Utile quand vous ne voulez **pas
exposer EPEL à des updates automatiques** (paquets pas toujours stables).

## 📚 Exercice 2 — `security: true` (patcher uniquement les CVE)

C'est **le pattern le plus utile** en production. Applique **uniquement** les
errata classés "Security Advisory" par le vendor RHEL.

```yaml
- name: Patcher uniquement les CVE
  ansible.builtin.dnf:
    name: '*'
    state: latest
    security: true
```

🔍 **Observation** :

- **`name: '*'`** = tous les paquets installés.
- **`state: latest`** = mettre à jour.
- **`security: true`** = **filtre** : seulement les paquets avec un errata de
  sécurité disponible.

**Conséquence** : sur 1000 paquets installés, peut-être 5-10 ont un patch
sécurité disponible — seuls ceux-là sont touchés. Les autres restent à leur
version courante.

**Combiner avec `bugfix: true`** pour les bugfixes :

```yaml
- name: Patcher securite ET bugs
  ansible.builtin.dnf:
    name: '*'
    state: latest
    security: true
    bugfix: true
```

## 📚 Exercice 3 — `exclude: kernel*` (préserver des paquets sensibles)

```yaml
- name: Mise a jour complete sauf kernel
  ansible.builtin.dnf:
    name: '*'
    state: latest
    exclude: kernel*
```

🔍 **Observation** : un upgrade kernel **nécessite un reboot**. Si vous appliquez
les patches de sécurité **sans reboot programmé**, `exclude: kernel*` évite de
mettre la machine en état "kernel staged but not running" (sécurité dégradée
jusqu'au prochain reboot).

**`exclude:` accepte une liste** :

```yaml
exclude:
  - kernel*
  - glibc
  - systemd
```

**Wildcards** : `kernel*` matche `kernel`, `kernel-headers`, `kernel-modules`,
`kernel-tools`, etc.

## 📚 Exercice 4 — `autoremove: true` (nettoyer les orphelins)

```yaml
- name: Installer un paquet avec dependances
  ansible.builtin.dnf:
    name: httpd
    state: present

- name: Desinstaller httpd ET ses dependances orphelines
  ansible.builtin.dnf:
    name: httpd
    state: absent
    autoremove: true
```

🔍 **Observation** : quand on désinstalle `httpd`, ses dépendances exclusives
(`apr`, `apr-util`, `httpd-tools`) deviennent **orphelines**. **`autoremove:
true`** les supprime automatiquement — comme `dnf autoremove` après un `dnf
remove`.

**Sans `autoremove`**, vous accumulez des paquets fantômes au fil des cycles
install/uninstall. Sur un système long-living, ça peut représenter 100+ paquets
inutiles.

## 📚 Exercice 5 — `update_cache: true` (refresh repos)

```yaml
- name: Refresh cache puis installer
  ansible.builtin.dnf:
    name: nginx
    state: latest
    update_cache: true
```

🔍 **Observation** : par défaut, DNF utilise un **cache de métadonnées** (TTL ~6h).
**`update_cache: true`** force un **refresh immédiat** — utile quand vous venez
de :

- Modifier un fichier `.repo` (nouveau repo ajouté).
- Pousser un nouveau paquet dans un **repo interne**.
- Activer un nouveau channel.

**Coût** : le refresh prend 5-30s selon les repos (CDN, network). À mettre **une
fois** en début de play, pas par tâche.

## 📚 Exercice 6 — `download_only: true` (pré-stage)

```yaml
- name: Pre-telecharger pour install offline
  ansible.builtin.dnf:
    name:
      - bind
      - dhcp-server
    state: present
    download_only: true
    download_dir: /var/cache/staged-rpms/
```

🔍 **Observation** : Ansible télécharge les RPM dans `download_dir` **sans les
installer**. Pattern utilisé pour :

- **Préparer un upgrade air-gapped** : télécharger sur un nœud connecté, pousser
  sur un nœud isolé via `copy:`.
- **Réduire la fenêtre de panne** : pré-stager 2h avant la maintenance, installer
  en 30s pendant la fenêtre.

## 📚 Exercice 7 — Le piège : `state: absent` + dépendance partagée

```yaml
- name: Desinstaller bind sans autoremove
  ansible.builtin.dnf:
    name: bind
    state: absent
    autoremove: true
```

🔍 **Observation** : `bind` dépend de `bind-libs` qui est **aussi utilisé** par
d'autres paquets (`bind-utils`, parfois `glibc`). `autoremove: true` peut
**supprimer trop de choses** si DNF estime que la dépendance est orpheline.

**Pattern défensif** : tester en `--check` d'abord, ou utiliser
`autoremove: false` pour ne pas toucher aux dépendances.

```bash
ansible-playbook labs/modules-paquets/dnf-options/lab.yml --check
# Verifier ce qui serait desinstalle avant de lancer pour de vrai
```

## 🔍 Observations à noter

- **`enablerepo:`** = activation **temporaire** d'un repo (sans modification
  persistante).
- **`security: true`** = pattern de **patching de production** (errata CVE
  uniquement).
- **`exclude: kernel*`** = éviter de stager un kernel sans reboot programmé.
- **`autoremove: true`** sur `state: absent` = nettoyage des dépendances
  orphelines (mais peut être trop agressif).
- **`update_cache: true`** = forcer refresh, à mettre **une fois** en début de
  play.
- **`download_only: true`** = pré-stage pour upgrades air-gapped ou maintenance
  courte.

## 🤔 Questions de réflexion

1. Vous voulez patcher 50 serveurs avec **uniquement les CVE critiques** sans
   redémarrer. Quel `dnf:` complet (combinaison `security`, `exclude`, `state`) ?

2. `autoremove: true` peut être dangereux. Quel pattern défensif (combinaison
   `--check`, `register`, `assert`) pour éviter une suppression inattendue ?

3. Quelle différence concrète entre `state: latest` (sans `security:`) et
   `state: latest + security: true` ? Donnez un exemple où cela change la liste
   des paquets touchés.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`name: '@web-server'`** : installation de **groupes** DNF (`@base`,
  `@minimal-environment`, `@web-server`). Pratique pour provisionner un rôle
  métier sans énumérer 30 paquets.
- **`releasever:`** : installer un paquet d'une **version majeure différente**
  (ex : RHEL 9 → RHEL 10). Avancé, à réserver aux migrations contrôlées.
- **`config_file:`** : utiliser un fichier `dnf.conf` custom (différent du
  défaut). Rare mais utile pour des images Docker.
- **Combinaison `download_only:` + `copy:`** : pattern d'upgrade air-gapped
  complet (download d'un côté, transfer SSH, install offline).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-paquets/dnf-options/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-paquets/dnf-options/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-paquets/dnf-options/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
