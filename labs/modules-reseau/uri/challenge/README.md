# 🎯 Challenge — Module `uri:` (appels API + parsing JSON)

## ✅ Objectif

Sur **db1.lab**, faire 2 appels HTTP avec **`ansible.builtin.uri`** :

| # | URL | Méthode | Particularité |
| --- | --- | --- | --- |
| 1 | `https://httpbin.org/json` | GET | Capture JSON, écrit vers `/opt/lab-uri-get.json` |
| 2 | `https://httpbin.org/post` | POST | Body JSON `{name: rhce, version: 2026}`, écrit la réponse vers `/opt/lab-uri-post.json` |

Pas de `command: curl`. Tout via le module Ansible.

## 🧩 Étapes

1. **GET** `https://httpbin.org/json` :
   - `return_content: true` pour capturer le body.
   - `register: get_response`.
   - **Écrire** `get_response.content` dans `/opt/lab-uri-get.json` via `copy:
     content:`.
2. **POST** `https://httpbin.org/post` avec body `{name: rhce, version: 2026}` :
   - `body_format: json`, `body:` un dict YAML.
   - `status_code: [200, 201]` (httpbin renvoie 200).
   - `register: post_response`.
   - **Écrire** `post_response.json | to_json` dans `/opt/lab-uri-post.json`.

## 🧩 Squelette

```yaml
---
- name: Challenge - uri (GET + POST)
  hosts: db1.lab
  become: true

  tasks:
    - name: GET sur httpbin /json
      ansible.builtin.uri:
        url: ???
        method: ???
        return_content: ???
      register: get_response

    - name: Sauver le body GET
      ansible.builtin.copy:
        content: ???
        dest: ???
        mode: "0644"

    - name: POST sur httpbin /post avec body JSON
      ansible.builtin.uri:
        url: ???
        method: ???
        body_format: ???
        body:
          name: rhce
          version: 2026
        status_code: ???
        return_content: ???
      register: post_response

    - name: Sauver le body POST (JSON pretty)
      ansible.builtin.copy:
        content: "{{ ??? | to_nice_json }}"
        dest: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`return_content: true`** (défaut `false`) : capture le body de la
>   réponse dans `<var>.content`. Sans, vous n'avez que le code HTTP +
>   headers.
> - **`status_code:`** = liste de codes acceptés. Par défaut `[200]`. Pour
>   accepter 200 ET 201 : `status_code: [200, 201]`.
> - **`body_format: json`** : sérialise le `body:` en JSON
>   automatiquement et set `Content-Type: application/json`. Sans, le
>   `body:` est traité comme string.
> - **`validate_certs:`** : `true` par défaut. Pour les certs
>   auto-signés en lab : `false` (anti-pattern en prod).

## 🚀 Lancement

```bash
ansible-playbook labs/modules-reseau/uri/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-uri-*.json"
ansible db1.lab -m ansible.builtin.command -a "head -5 /opt/lab-uri-get.json"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-reseau/uri/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/opt/lab-uri-get.json state=absent"
ansible db1.lab -b -m file -a "path=/opt/lab-uri-post.json state=absent"
```

## 💡 Pour aller plus loin

- **`until:` + `retries:` + `delay:`** : healthcheck applicatif — répéter
  l'appel jusqu'à ce qu'il réponde correctement (max N fois).
- **Authentification** : `url_username` / `url_password` (Basic) ou
  `headers: Authorization: Bearer ...` (OAuth/JWT).
- **`creates:`** : skip l'appel si un fichier existe déjà côté managed node
  (idempotence pour les POST de création).
- **`dest:`** : enregistre la réponse dans un fichier (équivalent à
  `register:` + `copy: content:`).
- **Lint** :

   ```bash
   ansible-lint labs/modules-reseau/uri/challenge/solution.yml
   ```
