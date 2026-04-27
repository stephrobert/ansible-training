# Lab 49 — Module `get_url:` (télécharger un fichier HTTP/HTTPS)

## 🧠 Rappel

🔗 [**Module get_url Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-get-url/)

`ansible.builtin.get_url:` télécharge un fichier depuis une URL HTTP/HTTPS/FTP
**directement sur le managed node** (pas de passage par le control node). C'est
le module n°1 RHCE 2026 pour récupérer un binaire upstream, une **release
applicative**, un **dépôt RPM** custom, ou un fichier de config externe.

Options critiques : **`url:`**, **`dest:`**, **`mode:`**, **`checksum:`**
(vérification d'intégrité), **`force: true`** (override), **`headers:`**
(authentification API), **`validate_certs:`** (TLS strict).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Télécharger** un fichier avec `get_url:` (idempotent par défaut).
2. **Vérifier l'intégrité** avec `checksum: sha256:...`.
3. **Authentifier** un download avec `url_username:` / `url_password:` ou
   `headers:`.
4. **Désactiver TLS strict** avec `validate_certs: false` (déconseillé en prod).
5. **Choisir** entre `get_url:` (simple download) et `uri:` (appel API JSON).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /opt/lab-download-* /tmp/lab-get-*"
```

## 📚 Exercice 1 — Téléchargement basique

```yaml
---
- name: Demo get_url simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Telecharger un fichier de test
      ansible.builtin.get_url:
        url: https://example.com/index.html
        dest: /opt/lab-download-example.html
        mode: "0644"
```

🔍 **Observation** :

- 1er run : `changed=1` — fichier téléchargé.
- 2e run : `changed=0` — Ansible vérifie l'**ETag** ou la **date de modification**
  HTTP. Si le serveur n'a pas changé, pas de re-download.

**Idempotence par défaut** : `get_url` ne re-télécharge **que si nécessaire**.
Pratique pour des artefacts versionnés où l'URL contient déjà la version
(`myapp-1.0.0.tar.gz`).

## 📚 Exercice 2 — Vérification d'intégrité (`checksum:`)

```yaml
- name: Telecharger node_exporter avec verification SHA256
  ansible.builtin.get_url:
    url: https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
    dest: /opt/node_exporter.tar.gz
    checksum: sha256:a550cd5c05f760b7934a2d0afad66d2e92e681482f5f57a917465b1fba3b02a6
    mode: "0644"
```

🔍 **Observation** :

- Si le fichier téléchargé a un SHA256 **différent** de celui spécifié, la tâche
  **failed**.
- Si **identique**, idempotent — pas de re-download.

**Formats supportés** :

- **`sha256:<hex>`** — recommandé (collision-résistant).
- **`sha512:<hex>`** — plus fort (overkill généralement).
- **`sha1:<hex>`** — déprécié pour la sécurité.
- **`md5:<hex>`** — ne **pas** utiliser (cassé cryptographiquement).
- **`sha256:https://example.com/SHA256SUMS`** — récupère la liste des sums
  depuis une URL et matche le filename.

**Pattern production** : **toujours** spécifier un checksum pour des binaires
critiques. Sans ça, un MITM ou un repo compromis pousserait n'importe quoi.

## 📚 Exercice 3 — Authentification

```yaml
# Authentification basique (HTTP Basic)
- ansible.builtin.get_url:
    url: https://repo.private.com/files/private.tar.gz
    dest: /opt/private.tar.gz
    url_username: "{{ vault_repo_user }}"
    url_password: "{{ vault_repo_password }}"
    mode: "0600"

# Token Bearer (API moderne)
- ansible.builtin.get_url:
    url: https://api.github.com/repos/myorg/myapp/releases/latest
    dest: /opt/release-meta.json
    headers:
      Authorization: "Bearer {{ vault_github_token }}"
      Accept: application/vnd.github+json
    mode: "0600"
```

🔍 **Observation** :

- **`url_username` / `url_password`** : HTTP Basic Auth.
- **`headers:`** : pour Bearer tokens, API keys custom, User-Agent.
- **`mode: "0600"`** sur fichiers contenant du contenu auth (license, token).

**Stockage des secrets** : **toujours** dans Ansible Vault (`vault_*` en
convention) — jamais hardcodé dans le playbook.

## 📚 Exercice 4 — `force: true` (override)

```yaml
- name: Forcer le re-download meme si checksum match
  ansible.builtin.get_url:
    url: https://example.com/dynamic-content.txt
    dest: /opt/lab-download-dynamic.txt
    force: true
    mode: "0644"
```

🔍 **Observation** : par défaut, `get_url` est idempotent — il ne re-télécharge
**pas** si le fichier existe déjà avec le bon contenu. **`force: true`** force
le download à chaque run.

**Cas d'usage** :

- Endpoint qui retourne du contenu **dynamique** (token CSRF, snapshot horaire).
- Re-télécharger pour **rotater** un artefact (ex : nouveau certif TLS).

## 📚 Exercice 5 — `validate_certs:` (TLS strict)

```yaml
- name: Telecharger depuis un certif self-signed (DEV uniquement)
  ansible.builtin.get_url:
    url: https://internal-dev.lab/file.tar.gz
    dest: /opt/file.tar.gz
    validate_certs: false   # DESACTIVE LE CHECK TLS — DANGER
    mode: "0644"
```

🔍 **Observation** : `validate_certs: false` désactive la vérification du
certificat TLS. **Risque MITM**.

**Cas légitimes** :

- Lab interne avec PKI self-signed (mais préférer ajouter le CA root au truststore).
- Test temporaire sur un environnement dev.

**Jamais en prod** : si vous voyez `validate_certs: false` en code de production,
c'est une **faille de sécurité** — corrigez le truststore ou utilisez un certif
valide (Let's Encrypt, internal CA).

## 📚 Exercice 6 — Combiner avec `unarchive:`

Pattern fréquent : télécharger un tarball + l'extraire en une chaîne.

```yaml
- name: Telecharger et extraire node_exporter
  block:
    - name: Telecharger
      ansible.builtin.get_url:
        url: https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
        dest: /tmp/node_exporter.tar.gz
        checksum: sha256:a550cd5c05f760b7934a2d0afad66d2e92e681482f5f57a917465b1fba3b02a6

    - name: Extraire dans /opt/
      ansible.builtin.unarchive:
        src: /tmp/node_exporter.tar.gz
        dest: /opt/
        remote_src: true
        creates: /opt/node_exporter-1.7.0.linux-amd64/node_exporter
```

🔍 **Observation** : alternative plus directe — `unarchive: src:` accepte des
URLs directement avec `remote_src: true`. Mais pas de `checksum:` côté
`unarchive:` — si l'intégrité compte, faire `get_url:` puis `unarchive:` séparément.

## 📚 Exercice 7 — Le piège : `url:` qui change vs contenu identique

```yaml
# La query string change a chaque run, mais le contenu serveur est identique
- ansible.builtin.get_url:
    url: "https://example.com/static.zip?cache_buster={{ ansible_date_time.epoch }}"
    dest: /opt/lab-download-static.zip
```

🔍 **Observation** : si l'URL change à chaque run (timestamp, token), Ansible ne
sait **pas** que le contenu est identique → **re-download à chaque run**.

**Mitigation** : utiliser `checksum:` sur le **contenu** :

```yaml
- ansible.builtin.get_url:
    url: "https://example.com/static.zip?cache_buster={{ ansible_date_time.epoch }}"
    dest: /opt/lab-download-static.zip
    checksum: sha256:abc123...
```

Avec checksum, Ansible compare le **contenu local** au checksum attendu — si
match, **skip** même si l'URL diffère.

## 🔍 Observations à noter

- **`get_url:`** télécharge **côté managed node** (pas via control node).
- **Idempotent par défaut** via ETag / Last-Modified HTTP.
- **`checksum: sha256:...`** pour vérification d'intégrité (mandatory en prod).
- **`headers:`** pour Bearer tokens et API keys.
- **`validate_certs: false`** = DANGER — uniquement en dev avec PKI interne.
- **URL dynamique** (timestamp, token) → utiliser `checksum:` pour idempotence.

## 🤔 Questions de réflexion

1. Vous téléchargez `myapp-1.0.0.tar.gz` (URL stable) puis `myapp-1.1.0.tar.gz`
   (URL différente). Comment **garder l'historique** des deux versions sur le
   managed node, et basculer entre elles ?

2. Pourquoi `checksum: sha256:...` est-il **plus sûr** que de comparer
   `Content-Length` HTTP ? Donnez 2 raisons.

3. `get_url:` télécharge un fichier de 5Go. La connexion coupe à 4Go. Quel est
   le comportement par défaut au prochain run ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`tmp_dest:`** : dossier temporaire de download (utile si `/tmp` est petit
  ou en tmpfs).
- **`backup: true`** : créer un backup du fichier précédent avant overwrite.
- **`timeout:`** : timeout HTTP en secondes (défaut 10).
- **Mirroring repo** : combinaison `get_url:` + `loop:` pour synchroniser
  N fichiers depuis un repo, idempotent.
- **Lab 50 (`uri:`)** : pour des appels **API REST** plutôt que des downloads
  de fichiers.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-reseau/get-url/lab.yml
ansible-lint labs/modules-reseau/get-url/challenge/solution.yml
ansible-lint --profile production labs/modules-reseau/get-url/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
