# Lab 14a — Custom facts (`facts.d/*.fact`, ansible_local)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Custom facts Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/)

Les **facts standards** (`ansible_distribution`, `ansible_default_ipv4`, etc.) sont collectés par le module **`setup`** au début de chaque play. Les **custom facts** étendent ce mécanisme : on dépose un script (Bash, Python ou JSON/INI statique) dans **`/etc/ansible/facts.d/<nom>.fact`** sur la cible, et Ansible le lit à chaque `gather_facts` et expose le résultat sous **`ansible_local.<nom>`**.

**Cas d'usage** : tagger un hôte avec son **rôle métier** (`web`, `db`, `cache`), exposer des données spécifiques à l'application (version déployée, hash du dernier déploiement), centraliser des informations propriétaires.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Déposer** un custom fact statique au format **INI** dans `/etc/ansible/facts.d/`.
2. **Déposer** un custom fact dynamique (script Bash exécutable retournant du **JSON**).
3. **Lire** un custom fact via `ansible_local.<nom>` dans un playbook.
4. **Filtrer** la sortie de `setup` pour ne garder que les `ansible_local`.
5. **Comprendre** quand utiliser custom facts vs `set_fact` vs `host_vars`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/etc/ansible/facts.d state=absent" 2>&1 | tail -2
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab14a-custom-facts.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Arborescence cible

```text
labs/ecrire-code/custom-facts/
├── README.md                       ← ce fichier (tuto guidé)
├── Makefile                        ← cible clean
└── challenge/
    ├── README.md                   ← consigne du challenge
    └── tests/
        └── test_custom_facts.py    ← tests pytest+testinfra
```

L'apprenant écrit lui-même `lab.yml` et `challenge/solution.yml`.

## 📚 Exercice 1 — Custom fact INI statique

Créer un fichier INI sur la cible. Format reconnu par Ansible :

```ini
; /etc/ansible/facts.d/server.fact (sur db1.lab)
[meta]
role = database
environment = production
managed_by = ansible

[deployment]
version = 1.4.2
deployed_on = 2026-04-27
```

Via Ansible (depuis le control node) :

```yaml
---
- hosts: db1.lab
  become: true
  gather_facts: false
  tasks:
    - name: Créer /etc/ansible/facts.d/
      ansible.builtin.file:
        path: /etc/ansible/facts.d
        state: directory
        mode: "0755"

    - name: Déposer le custom fact INI
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/server.fact
        mode: "0644"
        content: |
          [meta]
          role = database
          environment = production
          managed_by = ansible

          [deployment]
          version = 1.4.2
          deployed_on = 2026-04-27
```

Lancer :

```bash
ansible-playbook labs/ecrire-code/custom-facts/lab.yml
```

🔍 **Observation** : **`/etc/ansible/facts.d/`** est le chemin par défaut. Format `.fact`. Ansible lit le fichier au prochain `gather_facts: true` (ou `setup` ad-hoc).

## 📚 Exercice 2 — Lire le custom fact

```bash
ansible db1.lab -m ansible.builtin.setup -a "filter=ansible_local"
```

Sortie :

```yaml
db1.lab | SUCCESS => {
    "ansible_facts": {
        "ansible_local": {
            "server": {
                "deployment": {
                    "deployed_on": "2026-04-27",
                    "version": "1.4.2"
                },
                "meta": {
                    "environment": "production",
                    "managed_by": "ansible",
                    "role": "database"
                }
            }
        },
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false
}
```

🔍 **Observation cruciale** : la structure est **`ansible_local.<nom_fichier_sans_.fact>.<section>.<clé>`**. Le nom de fichier `server.fact` produit `ansible_local.server`, les sections INI deviennent des sous-clés. **Filter `ansible_local`** isole les custom facts.

## 📚 Exercice 3 — Utiliser le fact dans un playbook

```yaml
- hosts: db1.lab
  gather_facts: true               # ← obligatoire pour collecter ansible_local
  tasks:
    - name: Déposer un fichier paramétré par le custom fact
      ansible.builtin.copy:
        dest: /tmp/lab14a-custom-facts.txt
        content: |
          Hostname: {{ inventory_hostname }}
          Role: {{ ansible_local.server.meta.role }}
          Env: {{ ansible_local.server.meta.environment }}
          Deployment version: {{ ansible_local.server.deployment.version }}
        mode: "0644"
```

Sortie sur db1.lab :

```text
Hostname: db1.lab
Role: database
Env: production
Deployment version: 1.4.2
```

🔍 **Observation** : **`gather_facts: true`** (default `true` sauf si désactivé) est **obligatoire**. Sinon `ansible_local` est vide. Pour économiser le temps de gather sur les autres facts : **`gather_subset: '!all,local'`** ne collecte que les `ansible_local`.

## 📚 Exercice 4 — Custom fact dynamique (script Bash → JSON)

Créer un script exécutable qui retourne du JSON :

```bash
# /etc/ansible/facts.d/uptime.fact (mode 0755, exécutable)
#!/bin/bash
cat <<EOF
{
  "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
  "load_1min": "$(awk '{print $1}' /proc/loadavg)",
  "kernel": "$(uname -r)"
}
EOF
```

Via Ansible :

```yaml
- name: Déposer le custom fact dynamique
  ansible.builtin.copy:
    dest: /etc/ansible/facts.d/uptime.fact
    mode: "0755"                     # ← exécutable
    content: |
      #!/bin/bash
      cat <<EOF
      {
        "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
        "load_1min": "$(awk '{print $1}' /proc/loadavg)",
        "kernel": "$(uname -r)"
      }
      EOF
```

Vérifier :

```bash
ansible db1.lab -m ansible.builtin.setup -a "filter=ansible_local"
```

```yaml
"ansible_local": {
    "server": { ... },
    "uptime": {
        "kernel": "5.14.0-...",
        "load_1min": "0.05",
        "uptime_seconds": 3242
    }
}
```

🔍 **Observation** : Ansible **détecte automatiquement** si le fichier est exécutable (bit `+x`). Si oui, il l'exécute et parse la sortie comme JSON. Permet des facts **dynamiques** (uptime, load, statut d'un service local). Format alternatif accepté : YAML, INI. Le script peut être en Python, Perl, n'importe quel langage.

## 📚 Exercice 5 — Custom facts vs `set_fact` vs `host_vars`

| Mécanisme | Stockage | Persistance | Cas d'usage |
|-----------|----------|-------------|-------------|
| **Custom fact** (`facts.d/*.fact`) | Sur la cible | **Persistant** entre runs | Tag métier, rôle, version déployée |
| **`set_fact`** | En mémoire pendant le play | Détruit en fin de play | Calcul intermédiaire dans un playbook |
| **`host_vars/<host>.yml`** | Sur le control node (Git) | Versionné dans le repo | Config statique connue à l'avance |
| **Inventaire dynamique** | Source externe (Cloud, DB) | Re-collecté à chaque run | Cloud, K8s, NetBox, infra dynamique |

🔍 **Observation** : custom facts = **vérité côté cible** (la machine sait elle-même son rôle). `host_vars` = **vérité côté gestion** (le repo Git sait). Les deux peuvent coexister.

## 🔍 Observations à noter

- **`/etc/ansible/facts.d/<nom>.fact`** = chemin par défaut.
- **Format** : INI, JSON, YAML statique **OU** script exécutable retournant du JSON/YAML.
- **Lecture** : `ansible_local.<nom>.<section>.<clé>` après `gather_facts: true`.
- **`ansible -m setup -a "filter=ansible_local"`** isole les custom facts.
- **Bit exécutable** (`mode: 0755`) → Ansible exécute le script. Sinon le lit comme statique.
- **Pas testé directement** à l'EX294 mais utile en prod.

## 🤔 Questions de réflexion

1. Que se passe-t-il si **deux fichiers** dans `/etc/ansible/facts.d/` ont le même nom de section ?
2. Pourquoi placer un script de fact **exécutable en mode 0755** plutôt que 0644 ?
3. Comment **désactiver temporairement** la collecte des custom facts ? (Indice : `gather_subset: '!local'`).
4. Quel **risque sécurité** d'avoir un script exécutable dans `facts.d/` writable par un user non-root ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — déposer un custom fact INI **et** un custom fact script Bash, lire les deux dans un playbook qui dépose un fichier preuve.

## 💡 Pour aller plus loin

- **Custom path** : `/etc/ansible/facts.d/` est le défaut. Modifier avec `ansible.builtin.setup -a "fact_path=/custom/path"`.
- **Caching** : combiner custom facts + `fact_caching = jsonfile` dans `ansible.cfg` pour éviter de re-collecter à chaque run.
- **Module `set_fact: cacheable: true`** : alternative pour persister un fact côté cache (pas côté cible).
- **Lab 14** : facts standards et magic vars (prérequis).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/ecrire-code/custom-facts/lab.yml
ansible-lint --profile production labs/ecrire-code/custom-facts/challenge/solution.yml
```
