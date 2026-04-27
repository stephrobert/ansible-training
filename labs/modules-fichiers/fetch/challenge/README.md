# 🎯 Challenge — Collecter `os-release` avec `fetch:`

## ✅ Objectif

`fetch:` est l'**inverse** de `copy:` : il rapatrie un fichier du **managed
node** vers le **control node**. Ce challenge le démontre sur **2 hôtes**.

## 🧩 Tâches

### Play 1 — Collecte sur web1 ET db1

Cible : `hosts: web1.lab,db1.lab` (2 hôtes en pattern explicite).

Pour chaque hôte, **rapatrier `/etc/os-release`** dans un fichier local
nommé d'après le hostname court (sans `.lab`) :

| Hôte | Fichier collecté côté control node |
| --- | --- |
| `web1.lab` | `collected/web1-os-release.txt` |
| `db1.lab` | `collected/db1-os-release.txt` |

### Play 2 — Tag spécifique web1

Cible : `hosts: web1.lab` uniquement.

1. Écrire (`copy: content:`) le fichier `/etc/lab-tag.txt` sur web1 avec le
   contenu `RHCE-LAB-2026`.
2. Le rapatrier (`fetch:`) côté control node dans `collected/web1-tag.txt`.

## 🧩 Indices clés

- **`fetch:` avec `flat: true`** est ce qui permet de poser un fichier unique
  côté control node (sans le sous-arbre `<hostname>/<chemin>` que fetch crée
  par défaut).
- Pour interpoler le **hostname court** (sans `.lab`), utilisez :

  ```yaml
  "{{ inventory_hostname | regex_replace('\\.lab$', '') }}"
  ```

- Le `dest:` du fetch peut utiliser **`{{ inventory_dir }}/../collected/...`**
  pour rester relatif au repo, ou un chemin absolu côté control.

## 🧩 Squelette

```yaml
---
- name: Play 1 - collecte os-release sur 2 hôtes
  hosts: web1.lab,db1.lab
  become: true

  tasks:
    - name: Rapatrier /etc/os-release vers ./collected/<host>-os-release.txt
      ansible.builtin.fetch:
        src: ???
        dest: ???
        flat: ???

- name: Play 2 - tag spécifique web1
  hosts: web1.lab
  become: true

  tasks:
    - name: Écrire /etc/lab-tag.txt
      ansible.builtin.copy:
        content: ???
        dest: ???
        mode: "0644"

    - name: Rapatrier le tag
      ansible.builtin.fetch:
        src: ???
        dest: ???
        flat: ???
```

> 💡 **Pièges** :
>
> - **`fetch:`** copie **du managed node vers le control node** (inverse
>   de `copy:`). Pour les sauvegardes, audits, debug.
> - **`flat: true`** : pas de sous-dossier par hôte (le fichier est posé
>   directement dans `dest`). Sans, `dest/<hostname>/<src>` est créé.
> - **`fail_on_missing: true`** : échec si le fichier source absent. Par
>   défaut `false` — la tâche est marquée `skipped`.
> - **`dest/<hostname>/`** : permet de différencier les fetch de plusieurs
>   hôtes. Ne pas combiner avec `flat: true`.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-fichiers/fetch/challenge/solution.yml
ls -la collected/
cat collected/web1-tag.txt
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-fichiers/fetch/challenge/tests/
```

Le test inspecte des fichiers **côté control node** (pas testinfra/SSH).

## 🧹 Reset

```bash
make -C labs/modules-fichiers/fetch clean
```

## 💡 Pour aller plus loin

- **`fetch: flat: false`** (défaut) : Ansible crée
  `dest/<hostname>/<chemin_complet>`. Utile pour préserver l'arborescence
  d'origine lors d'un audit multi-host.
- **Cas d'usage typique** : collecte de logs, dump de configs, snapshots
  pré-déploiement. Combinez avec `synchronize:` pour des dossiers entiers.
- **Lint** :

   ```bash
   ansible-lint labs/modules-fichiers/fetch/challenge/solution.yml
   ```
