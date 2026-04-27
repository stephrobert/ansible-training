# 🎯 Challenge — Refactorer un playbook non idempotent

## ✅ Objectif

Écrire un playbook qui **passe le test d'idempotence** : `changed=0` au second passage. Trois opérations à enchaîner sur `db1.lab`, chacune **idempotente** :

| # | Action | Module recommandé | Garde idempotence |
| --- | --- | --- | --- |
| 1 | Créer `/tmp/lab91-marker` avec contenu | `ansible.builtin.shell` | `creates:` |
| 2 | Poser `max_connections = 200` dans `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Lire la version curl et la stocker dans `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` sur la lecture |

**Critère** : second passage de `solution.yml` retourne `changed=0`.

## 🧩 Indices

### Squelette `solution.yml`

```yaml
---
- name: Challenge 91 — playbook idempotent
  hosts: ???
  become: ???
  gather_facts: false

  tasks:
    - name: Tâche 1 — créer marker
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
      args:
        creates: ???              # ← chemin du fichier marker

    - name: Tâche 2 — poser max_connections
      ansible.builtin.lineinfile:
        path: /tmp/lab91-config.cfg
        regexp: ???               # ← regex pour matcher la ligne
        line: ???
        create: ???
        mode: "0644"

    - name: Tâche 3a — lire la version curl
      ansible.builtin.command: curl --version
      register: curl_version
      changed_when: ???           # ← lecture seule

    - name: Tâche 3b — stocker la sortie
      ansible.builtin.copy:
        dest: /tmp/lab91-curl.txt
        content: "{{ curl_version.stdout_lines[0] }}\n"
        mode: "0644"
```

### Test d'idempotence manuel

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml | grep -E 'changed=|ok='
# → changed=0 attendu sur le 2e run
```

> 💡 **Pièges** :
>
> - **`shell:` / `command:` sans `creates:` ou `changed_when:`** : marqué
>   `changed=1` à chaque run → casse l'idempotence du play. Cause
>   principale d'un test "changed=0 au 2e run" qui échoue.
> - **`pipelining = True`** dans `ansible.cfg` : 30-50 % de speedup. Mais
>   incompatible avec `requiretty` dans sudoers — vérifier le sudoers
>   avant.
> - **`fact_caching = jsonfile`** + TTL 1h : évite de re-collecter les
>   facts à chaque run. Gain 1-3 sec par hôte.
> - **`forks` (défaut 5)** : augmenter à 10-20 sur un control node
>   correct. Plus de parallélisme = run plus court sur grand inventaire.
> - **`strategy: free`** : chaque hôte avance indépendamment, plus rapide
>   que `linear` mais sortie moins lisible.

## 🚀 Lancement

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/troubleshooting/idempotence-perfs/ clean
```

## 💡 Pour aller plus loin

- **`ansible-lint --profile production`** détecte les `command`/`shell` sans `changed_when:`.
- **Pre-commit hook `ansible-lint`** dans le repo pour bloquer les régressions.
- **Mode `--check --diff`** pour prévisualiser les changements sans appliquer.
