# 🎯 Challenge — Module `get_url:` (téléchargement avec checksum)

## ✅ Objectif

Sur **db1.lab**, télécharger 2 fichiers depuis Internet avec **vérification
d'intégrité** (sha256), permissions strictes, et idempotence garantie.

| Tâche | URL | Destination | Particularité |
| --- | --- | --- | --- |
| Page de test 1 | `https://www.gnu.org/licenses/gpl-3.0.txt` | `/opt/lab-gpl3.txt` | Mode 0644 |
| Page de test 2 | `https://www.gnu.org/licenses/lgpl-3.0.txt` | `/opt/lab-lgpl3.txt` | Mode 0644 + `force: false` |

Utiliser **`ansible.builtin.get_url`**. Pas de `command: curl` ni de `command: wget`.

## 🧩 Étapes

1. **Télécharger** `gpl-3.0.txt` dans `/opt/lab-gpl3.txt` (mode 0644).
2. **Télécharger** `lgpl-3.0.txt` dans `/opt/lab-lgpl3.txt` (mode 0644) avec
   `force: false` (ne pas re-télécharger si présent).
3. **Vérifier** qu'un 2ᵉ run du playbook ne retélécharge **pas** (idempotence).

## 🧩 Squelette

```yaml
---
- name: Challenge - get_url
  hosts: db1.lab
  become: true

  tasks:
    - name: Telecharger la GPL v3
      ansible.builtin.get_url:
        url: ???
        dest: ???
        mode: ???

    - name: Telecharger la LGPL v3 (force: false)
      ansible.builtin.get_url:
        url: ???
        dest: ???
        mode: ???
        force: ???
```

> 💡 **Pièges** :
>
> - **`force: false`** (défaut) : si `dest` existe, ne re-télécharge pas.
>   Idempotent. Avec `force: true`, re-télécharge à chaque run.
> - **`checksum:`** : format `algo:hash` (ex
>   `sha256:abc123…`). Si checksum invalide → tâche échoue ET
>   fichier supprimé. Sécurité supply-chain.
> - **`url:` HTTPS uniquement** en prod. Sans `validate_certs: true`
>   (défaut), Ansible refuse les certs auto-signés. Surcharger avec
>   `validate_certs: false` UNIQUEMENT en dev.
> - **Proxy d'entreprise** : `environment: { http_proxy: '...', https_proxy: '...' }`
>   au niveau task ou play.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-reseau/get-url/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
ansible db1.lab -m ansible.builtin.command -a "wc -l /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-reseau/get-url/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/opt/lab-gpl3.txt state=absent"
ansible db1.lab -b -m file -a "path=/opt/lab-lgpl3.txt state=absent"
```

## 💡 Pour aller plus loin

- **`checksum: sha256:...`** : vérification d'intégrité après download. Hors
  du scope de ce challenge mais **mandatory en production** pour des binaires
  critiques.
- **`headers:`** : injection de Bearer tokens / API keys pour endpoints
  authentifiés. Stocker les secrets dans **Ansible Vault**.
- **`validate_certs: false`** : désactive le check TLS. À **proscrire** en
  prod — préférer ajouter le CA root au truststore.
- **`get_url:` + `unarchive:`** : enchaînement classique pour télécharger +
  extraire un release upstream (avec `creates:` pour idempotence).
- **Lint** :

   ```bash
   ansible-lint labs/modules-reseau/get-url/challenge/solution.yml
   ```
