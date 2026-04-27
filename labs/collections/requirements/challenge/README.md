# 🎯 Challenge — `requirements.yml` multi-sources

## ✅ Objectif

Écrire un **`requirements.yml`** qui combine **3 sources** différentes, l'installer dans `local_collections/`, et déposer la liste des collections installées sur `db1.lab`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab94-collections.txt` |
| Permissions | `0644`, owner `root` |
| Nombre de collections installées | **≥ 3** |
| Sources requises | Galaxy + Git + (URL **ou** dir) |
| Pinning | **Strict** (semver `version: "X.Y.Z"` ou tag Git) |

## 🧩 Indices

### Étape 1 — `requirements.yml` (à créer dans `challenge/`)

```yaml
---
collections:
  # Source 1 : Galaxy
  - name: ???
    version: ???

  # Source 2 : Git (avec tag)
  - name: https://github.com/ansible-collections/community.docker.git
    type: ???
    version: ???

  # Source 3 : URL ou dir (au choix)
  - name: ???
    type: ???
```

### Étape 2 — `solution.yml` qui orchestre l'installation

```yaml
---
- name: Challenge 94 — installer collections + déposer inventaire
  hosts: db1.lab
  become: true
  gather_facts: false

  tasks:
    - name: Installer les collections du requirements.yml
      ansible.builtin.command: >-
        ansible-galaxy collection install
        -r {{ playbook_dir }}/requirements.yml
        -p {{ playbook_dir }}/../local_collections
        --force
      delegate_to: localhost
      become: false
      changed_when: ???

    - name: Lister les collections installées localement
      ansible.builtin.command: >-
        ansible-galaxy collection list
        -p {{ playbook_dir }}/../local_collections
      delegate_to: localhost
      become: false
      register: ???
      changed_when: ???

    - name: Déposer le fichier preuve sur db1.lab
      ansible.builtin.copy:
        dest: /tmp/lab94-collections.txt
        content: ???
        owner: ???
        group: ???
        mode: ???
```

### Étape 3 — Lancement

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

> 💡 **Pièges** :
>
> - **`requirements.yml`** (collections) ≠ **`requirements.txt`**
>   (Python). Convention historique : les deux peuvent coexister dans
>   un projet Ansible.
> - **Pinning `version:`** : sans, vous risquez un build cassé quand la
>   collection bumpe en major (breaking change). Toujours pin en prod.
> - **`-r requirements.yml`** vs **`collections:`** dans `ansible-galaxy
>   install` : la 2ᵉ syntaxe (clé YAML) est moderne. Ne pas mélanger.
> - **`signatures:`** sur les collections (Ansible 2.13+) : vérification
>   GPG. Renforce la supply chain. Format : URLs vers fichier `.sig`.

## 🚀 Lancement

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/requirements/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab94-collections.txt` existe avec mode `0644` et owner `root`.
- Au moins 3 collections listées dans le fichier.
- Au moins une collection avec un FQCN (point dans le namespace).

## 🧹 Reset

```bash
make -C labs/collections/requirements/ clean
```

## 💡 Pour aller plus loin

- **Signatures GPG** : ajouter `signatures:` à une collection + `--keyring` au lancement.
- **Renovate** : configurer un bot pour bumper auto `version: "X.Y.Z"` à chaque release upstream.
- **`ansible-lint --profile production`** : zéro warning attendu.
