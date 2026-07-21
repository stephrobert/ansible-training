# 🎯 Challenge — Module `uri:` (appels API + parsing JSON)

## ✅ Objectif

Sur **db1.lab**, faire 2 appels HTTP avec **`ansible.builtin.uri`** vers l'API
d'inventaire interne du lab, servie par **`api-interne.lab:8009`** :

| # | URL | Méthode | Particularité |
| --- | --- | --- | --- |
| 1 | `http://api-interne.lab:8009/api/reference` | GET | Capture JSON, écrit vers `/opt/lab-uri-get.json` |
| 2 | `http://api-interne.lab:8009/api/noeuds` | POST | Body JSON `{name: rhce, version: 2026}`, écrit la réponse vers `/opt/lab-uri-post.json` |

Pas de `command: curl`. Tout via le module Ansible.

> 🔎 **L'API tourne dans le lab, pas sur Internet.** `setup.yaml` la monte
> (nginx sur web2.lab) et publie le nom `api-interne.lab` dans le `/etc/hosts`
> de db1. Le lab n'a donc besoin d'aucun accès sortant. Le serveur **journalise
> chaque appel** : les tests relisent ce journal, et voient donc si la requête
> est réellement partie, et avec quel agent.

## 🧩 Étapes

1. **GET** `http://api-interne.lab:8009/api/reference` :
   - `return_content: true` pour capturer le body.
   - `register: get_response`.
   - **Écrire** `get_response.content` dans `/opt/lab-uri-get.json` via `copy:
     content:`.
2. **POST** `http://api-interne.lab:8009/api/noeuds` avec body
   `{name: rhce, version: 2026}` :
   - `body_format: json`, `body:` un dict YAML.
   - **`status_code: [200, 201]`** : l'API répond **201 (Created)**. Le défaut
     du module est `[200]` : sans cette ligne, la tâche **échoue**.
   - `register: post_response`.
   - **Écrire** `post_response.json | to_nice_json` dans `/opt/lab-uri-post.json`.

## 🧩 Squelette

```yaml
---
- name: Challenge - uri (GET + POST)
  hosts: db1.lab
  become: true

  tasks:
    - name: GET sur l endpoint de reference
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

    - name: POST pour declarer le noeud, avec body JSON
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
> - **`status_code:`** = liste de codes acceptés. Par défaut `[200]`. L'API de
>   ce lab répond **201** sur le POST : `status_code: [200, 201]` n'est pas
>   décoratif, c'est ce qui fait passer la tâche.
> - **`body_format: json`** : sérialise le `body:` en JSON
>   automatiquement et set `Content-Type: application/json`. Sans, le
>   `body:` est traité comme string.
> - **Les réponses de cette API sont déterministes** : deux appels rendent
>   exactement les mêmes octets. Vous pouvez donc écrire la réponse entière
>   sans casser l'idempotence. Face à une vraie API publique, méfiance : un
>   identifiant de trace ou un horodatage dans la réponse rendrait le `copy:`
>   `changed` à chaque passage.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-reseau/uri/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-uri-*.json"
ansible db1.lab -m ansible.builtin.command -a "head -5 /opt/lab-uri-get.json"
# Le serveur a-t-il vu passer vos appels ?
ansible web2.lab -b -m ansible.builtin.command -a "cat /var/log/nginx/lab-uri-api.log"
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
  `headers: Authorization: Bearer ...` (OAuth/JWT). Le lab `get-url` en fait
  la démonstration sur un dépôt interne protégé.
- **`creates:`** : skip l'appel si un fichier existe déjà côté managed node
  (idempotence pour les POST de création).
- **`dest:`** : enregistre la réponse dans un fichier (équivalent à
  `register:` + `copy: content:`).
- **Lint** :

   ```bash
   ansible-lint labs/modules-reseau/uri/challenge/solution.yml
   ```
