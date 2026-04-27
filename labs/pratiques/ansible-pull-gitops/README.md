# Lab 98 — `ansible-pull` : pattern GitOps / Edge (hors RHCE EX294)

> ⚠️ **Hors RHCE EX294** : ce lab couvre un pattern utile en production
> moderne (Edge, GitOps, IoT) mais **non testé** à l'examen RHCE 2026.
> À voir après avoir maîtrisé les bases push SSH classiques.

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Mode pull avec ansible-pull (GitOps Edge)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ansible-pull-gitops/)

Ansible fonctionne par défaut en mode **push** : un control node SSH vers les cibles. Mais il existe un mode **pull** : la cible **récupère son playbook depuis un repo Git** (avec **`ansible-pull`**) et **s'exécute elle-même**. Pas besoin de control node centralisé. Pas besoin d'accès SSH inverse.

**Cas d'usage 2026** :

- **Edge computing / IoT** : nœuds isolés derrière un NAT, sans IP publique, qui tirent leur config.
- **Bootstrap immuable** : intégration dans **cloud-init** pour qu'une VM provisionnée se configure au premier boot.
- **Scaling massif (>1000 nœuds)** : éviter le goulot d'étranglement du control node.
- **Pattern GitOps** : la **branche Git** est la source de vérité, chaque nœud reflète l'état du repo.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Comprendre** la différence push vs pull (qui initie la connexion).
2. **Lancer** `ansible-pull` manuellement contre un repo Git public.
3. **Configurer** une exécution périodique via **`cron`** ou **systemd timer**.
4. **Intégrer** `ansible-pull` dans **`cloud-init`** pour bootstrap au boot.
5. **Comprendre** les **limites** : pas de centralisation des logs, pas de control node, pas d'AAP Tower.
6. **Choisir** push vs pull selon le cas d'usage.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible-pull --version
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab98-pull-marker.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/pratiques/ansible-pull-gitops/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
├── repo-pull/                      ← (à créer) faux repo Git local
│   ├── pull-playbook.yml
│   └── README.md
└── challenge/
    ├── README.md                   ← consigne du challenge
    └── tests/
        └── test_pull.py            ← tests structurels
```

L'apprenant écrit lui-même le `pull-playbook.yml` + `challenge/solution.sh` (script qui orchestre `ansible-pull`).

## 📚 Exercice 1 — Push vs Pull

| Critère | Mode **push** (default) | Mode **pull** (`ansible-pull`) |
|---------|-------------------------|-------------------------------|
| Qui initie la connexion ? | Control node → cibles (SSH) | Cible → repo Git (HTTPS/SSH) |
| Centralisation | Oui (control node) | Non (chaque nœud autonome) |
| Visibilité logs | Centralisée | Distribuée (chaque nœud localement) |
| Cas d'usage typique | Datacenter, fleet maîtrisée | Edge, IoT, NAT, bootstrap |
| Compatible AAP Tower | Oui | Non (mode pur ansible-core) |
| Support FQCN, collections, vault | Oui | Oui |

🔍 **Observation** : `ansible-pull` **utilise les mêmes playbooks** qu'`ansible-playbook`. La **différence est juste qui exécute**, pas le contenu du playbook. Permet de **basculer** un projet push vers pull sans réécriture.

## 📚 Exercice 2 — `ansible-pull` minimal

Sur **db1.lab** (la cible exécute elle-même) :

```bash
sudo dnf install -y ansible-core git

# Lancer ansible-pull contre un repo Git public
ansible-pull \
  -U https://github.com/stephrobert/ansible-pull-demo.git \
  -d /var/lib/ansible-pull \
  pull-playbook.yml
```

Ce que fait `ansible-pull` :

1. `git clone` (ou `git pull` si déjà clôné) le repo dans `/var/lib/ansible-pull/`.
2. `ansible-playbook` sur **`pull-playbook.yml`** avec `hosts: localhost` (par défaut).
3. Exit avec le code de retour du playbook.

🔍 **Observation** : `-U <git-url>` est l'argument obligatoire. **`-d <chemin>`** localise le clone (default `/var/lib/ansible/local`). **`pull-playbook.yml`** est le nom du playbook à l'intérieur du repo (default `local.yml`).

## 📚 Exercice 3 — Repo Git local pour le lab

Comme on n'a pas de repo Git distant pour le lab, on simule avec un **dossier local** :

```bash
# Créer un faux "repo" local (en pratique : repo Git avec push origin)
mkdir -p labs/pratiques/ansible-pull-gitops/repo-pull
cat > labs/pratiques/ansible-pull-gitops/repo-pull/pull-playbook.yml <<'EOF'
---
- hosts: localhost
  connection: local
  become: true
  gather_facts: false
  tasks:
    - name: Marker pull executed
      ansible.builtin.copy:
        dest: /tmp/lab98-pull-marker.txt
        content: |
          ansible-pull executed at: {{ ansible_date_time.iso8601 | default('unknown') }}
          hostname: {{ ansible_hostname | default('localhost') }}
        mode: "0644"
EOF

cd labs/pratiques/ansible-pull-gitops/repo-pull/
git init && git add . && git -c user.email=a@b -c user.name=lab commit -m "initial"
```

Lancer `ansible-pull` avec cette source locale (depuis db1.lab) :

```bash
ssh ansible@db1.lab "
  sudo dnf install -y ansible-core git
  sudo ansible-pull -U /home/bob/Projets/ansible-training/labs/pratiques/ansible-pull-gitops/repo-pull \
    -d /var/lib/ansible-pull \
    pull-playbook.yml
"
```

🔍 **Observation** : pour la démo on utilise un chemin local. En prod, c'est **`https://github.com/...`** ou **`git@gitlab.com:...`** avec une **clé SSH déployée** sur le nœud (typiquement via cloud-init).

## 📚 Exercice 4 — Exécution périodique via cron

Pattern courant : cron toutes les 30 minutes pour synchroniser avec le repo.

```cron
# /etc/cron.d/ansible-pull
*/30 * * * * root /usr/bin/ansible-pull \
  -U https://github.com/myorg/infra.git \
  -d /var/lib/ansible-pull \
  pull-playbook.yml \
  >> /var/log/ansible-pull.log 2>&1
```

Via Ansible (push initial qui configure le pull) :

```yaml
- name: Configurer ansible-pull en cron
  ansible.builtin.cron:
    name: ansible-pull
    user: root
    minute: "*/30"
    job: >-
      /usr/bin/ansible-pull
      -U https://github.com/myorg/infra.git
      -d /var/lib/ansible-pull
      pull-playbook.yml
      >> /var/log/ansible-pull.log 2>&1
```

🔍 **Observation** : pattern **bootstrap puis pull** : (1) push initial pour installer ansible-core + déposer le cron, (2) ensuite le nœud s'**auto-configure** depuis le repo. L'agent reste minimaliste.

## 📚 Exercice 5 — Intégration cloud-init

```yaml
# user-data cloud-init
#cloud-config
packages:
  - ansible-core
  - git

runcmd:
  - ansible-pull -U https://github.com/myorg/infra.git pull-playbook.yml
```

🔍 **Observation** : pattern **immuable / Edge**. Une nouvelle VM se **boote** avec cloud-init → `ansible-pull` exécute le playbook depuis Git → la VM est **prête sans intervention**. À combiner avec une clé déploy SSH dans cloud-init pour les repos privés.

## 📚 Exercice 6 — Limites du mode pull

| Limitation | Impact |
|------------|--------|
| **Pas de centralisation** | Les logs sont sur chaque nœud (`/var/log/ansible-pull.log`) — agréger via journalctl + rsyslog vers un Loki/ELK central. |
| **Pas d'AAP Tower** | Si vous voulez le UI AAP, restez en push. AAP est strictement push. |
| **Auto-update du nœud lui-même** | Risque si un commit casse `ansible-pull` lui-même → nœud bloqué. Tester en CI avant de merger sur `main`. |
| **Drift indétectable depuis le centre** | Pas de "PLAY RECAP" agrégé. Un nœud isolé peut diverger sans alerter. |

🔍 **Observation** : le pattern **push reste le défaut** pour la plupart des fleets. **Pull** = niche **Edge / IoT / GitOps strict**. L'EX294 ne le teste pas car il vise les **datacenters Red Hat classiques**.

## 🔍 Observations à noter

- **Push** = control node → cibles (SSH). Default. AAP Tower compatible.
- **Pull** = cible → repo Git. `ansible-pull -U <url>`. Non testé EX294.
- **Cron / systemd timer** pour exécution périodique.
- **`cloud-init` + `ansible-pull`** = pattern bootstrap immuable.
- **Pas de centralisation** des logs — agréger via syslog/Loki/ELK.
- Compatibles avec FQCN, collections, vault, all standard Ansible.

## 🤔 Questions de réflexion

1. Pourquoi `ansible-pull` est-il **plus adapté à l'IoT** que le push SSH classique ?
2. Quel risque sécurité d'exécuter `ansible-pull` sur un repo Git **non signé** ?
3. Comment **agréger les logs** de 100 nœuds pull dans un ELK central ?
4. Pourquoi AAP / Automation Controller ne supporte pas le mode pull ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — créer un mini-repo Git local + lancer `ansible-pull` depuis db1.lab pour qu'il dépose un fichier preuve.

## 💡 Pour aller plus loin

- **Lab 92 → 100 (mock RHCE)** : pratique du **push** classique.
- **`ansible-pull --vault-password-file`** : compatible avec Vault.
- **systemd timer** : alternative à cron, meilleur logging via journalctl.
- **GitOps Ansible** : combiner `ansible-pull` + Argo Events / Flux pour réagir aux push Git.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/pratiques/ansible-pull-gitops/repo-pull/pull-playbook.yml
```

> 💡 **Astuce** : `ansible-lint` valide le `pull-playbook.yml` exactement comme un playbook normal (`hosts: localhost`, `connection: local`).
