# 🎯 Challenge — Module `get_url:` (téléchargement avec checksum)

## ✅ Objectif

Sur **db1.lab**, télécharger 2 fichiers depuis le **dépôt de référence interne**
du lab, servi par `depot-interne.lab:8008`, avec **vérification d'intégrité**
(sha256), **authentification**, permissions strictes et idempotence garantie.

| Tâche | URL | Destination | Particularité |
| --- | --- | --- | --- |
| Texte public | `http://depot-interne.lab:8008/depot/gpl-3.0.txt` | `/opt/lab-gpl3.txt` | Mode 0644 + `checksum:` sha256 |
| Texte protégé | `http://depot-interne.lab:8008/prive/lgpl-3.0.txt` | `/opt/lab-lgpl3.txt` | Mode 0644 + `force: false` + **Basic Auth** |

Utiliser **`ansible.builtin.get_url`**. Pas de `command: curl` ni de `command: wget`.

> 🔎 **Le dépôt tourne dans le lab, pas sur Internet.** `setup.yaml` le monte
> (nginx sur web2.lab) et publie le nom `depot-interne.lab` dans le `/etc/hosts`
> de db1. Le lab n'a besoin d'aucun accès sortant. Le serveur **journalise
> chaque requête** : les tests relisent ce journal et voient donc si vous avez
> réellement vérifié l'intégrité, et avec quel agent vous avez téléchargé.

### 🔑 Accès à la zone protégée

| Utilisateur | Mot de passe |
| --- | --- |
| `depot` | `rhce2026` |

Le mot de passe est en clair ici parce que le sujet de ce lab est `get_url`.
En production il vivrait dans **Ansible Vault** : c'est l'objet de la section
« vault » de la formation.

## 🧩 Étapes

1. **Télécharger** `gpl-3.0.txt` dans `/opt/lab-gpl3.txt` (mode 0644), en
   **vérifiant son empreinte sha256**. Le dépôt publie les sommes à côté du
   fichier, en `http://depot-interne.lab:8008/depot/gpl-3.0.txt.sha256` :
   pointez-le avec `checksum: sha256:<url>`, ne recopiez pas une empreinte à la
   main. C'est ainsi que fonctionne un miroir sérieux, et c'est ce qui rend le
   playbook juste même quand le fichier amont change de version.
2. **Télécharger** `lgpl-3.0.txt` dans `/opt/lab-lgpl3.txt` (mode 0644) depuis
   la zone protégée : sans identifiants, le serveur rend **401** et la tâche
   échoue. Ajouter `force: false` (ne pas re-télécharger si présent).
3. **Vérifier** qu'un 2ᵉ run du playbook ne retélécharge **pas** (idempotence).

## 🧩 Squelette

```yaml
---
- name: Challenge - get_url
  hosts: db1.lab
  become: true

  tasks:
    - name: Telecharger la GPL v3 en verifiant son integrite
      ansible.builtin.get_url:
        url: ???
        dest: ???
        checksum: ???
        mode: ???

    - name: Telecharger la LGPL v3 depuis la zone protegee (force: false)
      ansible.builtin.get_url:
        url: ???
        dest: ???
        url_username: ???
        url_password: ???
        force_basic_auth: ???
        mode: ???
        force: ???
```

> 💡 **Pièges** :
>
> - **`force: false`** (défaut) : si `dest` existe, ne re-télécharge pas.
>   Idempotent. Avec `force: true`, re-télécharge à chaque run.
> - **`checksum:`** : format `algo:hash` (ex `sha256:abc123…`) **ou
>   `algo:url`** (ex `sha256:http://…/fichier.sha256`), et c'est cette seconde
>   forme qu'on veut ici. Si l'empreinte ne correspond pas → tâche en échec ET
>   fichier supprimé. Sécurité supply-chain : un miroir compromis ne passe pas.
> - **`force_basic_auth: true`** : envoie l'en-tête `Authorization` dès la
>   première requête. Sans lui, Ansible attend le 401 du serveur avant de
>   retenter avec les identifiants : cela marche aussi, mais coûte un
>   aller-retour.
> - **`validate_certs:`** : `true` par défaut. Le dépôt du lab est en HTTP
>   simple, la question ne se pose pas ici ; face à un cert auto-signé en dev :
>   `false` (anti-pattern en prod).
> - **Proxy d'entreprise** : `environment: { http_proxy: '...', https_proxy: '...' }`
>   au niveau task ou play.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-reseau/get-url/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
ansible db1.lab -m ansible.builtin.command -a "wc -l /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
# Le depot a-t-il vu passer vos requetes ?
ansible web2.lab -b -m ansible.builtin.command -a "cat /var/log/nginx/lab-get-url-depot.log"
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

- **`headers:`** : injection de Bearer tokens / API keys pour endpoints
  authentifiés. Stocker les secrets dans **Ansible Vault**.
- **`validate_certs: false`** : désactive le check TLS. À **proscrire** en
  prod — préférer ajouter le CA root au truststore.
- **`get_url:` + `unarchive:`** : enchaînement classique pour télécharger +
  extraire un release upstream (avec `creates:` pour idempotence).
- **`uri:`** : pour appeler une API REST plutôt que télécharger un fichier.
  C'est l'objet du lab suivant.
- **Lint** :

   ```bash
   ansible-lint labs/modules-reseau/get-url/challenge/solution.yml
   ```
