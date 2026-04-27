# Lab 50 — Module `uri:` (appels API REST)

## 🧠 Rappel

🔗 [**Module uri Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-uri/)

`ansible.builtin.uri:` fait des appels **HTTP/HTTPS** depuis le managed node :
GET, POST, PUT, DELETE. C'est l'équivalent d'un `curl` mais avec **idempotence
explicite**, parsing **JSON automatique**, et **gestion d'erreurs** structurée.

Cas d'usage RHCE 2026 : healthchecks applicatifs, **création de ressources**
via API (Kubernetes, Vault, Grafana), **récupération de tokens** OAuth,
notifications webhook (Slack, Teams).

Options critiques : **`url:`**, **`method:`** (GET défaut), **`status_code:`**
(liste de codes acceptés), **`return_content: true`** (capture la réponse),
**`body:`** + **`body_format:`** (json/form-urlencoded/raw), **`headers:`**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Faire un GET** simple et capturer la réponse (`return_content: true`).
2. **Faire un POST** avec body JSON (`body_format: json`).
3. **Authentifier** via `url_username`/`url_password` (Basic) ou `headers:`
   (Bearer).
4. **Accepter plusieurs codes** de retour (`status_code: [200, 201, 204]`).
5. **Distinguer** `uri:` (API REST) de `get_url:` (download de fichier).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — GET simple + capture de réponse

```yaml
---
- name: Demo uri GET
  hosts: db1.lab
  tasks:
    - name: Recuperer un fichier JSON public
      ansible.builtin.uri:
        url: https://api.github.com/repos/ansible/ansible/releases/latest
        method: GET
        return_content: true
      register: api_response

    - name: Afficher la version (parsing JSON automatique)
      ansible.builtin.debug:
        msg: "Derniere release Ansible : {{ api_response.json.tag_name }}"

    - name: Afficher quelques champs
      ansible.builtin.debug:
        msg: |
          name : {{ api_response.json.name }}
          tag : {{ api_response.json.tag_name }}
          published : {{ api_response.json.published_at }}
```

🔍 **Observation** :

- **`return_content: true`** capture la réponse dans `register.content` (raw)
  ET `register.json` (parsé si `Content-Type: application/json`).
- **Pas besoin de `from_json`** — Ansible parse automatiquement les réponses
  JSON.
- **`method: GET`** est le défaut — on peut l'omettre.

## 📚 Exercice 2 — POST avec body JSON

```yaml
- name: Creer une ressource via POST
  ansible.builtin.uri:
    url: https://httpbin.org/post
    method: POST
    body_format: json
    body:
      name: "myapp"
      version: "1.0.0"
      env: "prod"
    status_code: [200, 201]
    return_content: true
  register: post_result

- name: Afficher echo de la requete (httpbin renvoie le body recu)
  ansible.builtin.debug:
    msg: "Server vu : {{ post_result.json.json }}"
```

🔍 **Observation** :

- **`body_format: json`** sérialise automatiquement le dict Ansible en JSON
  pour le body HTTP.
- **`status_code: [200, 201]`** : la tâche **réussit** si le serveur retourne
  200 OU 201. Sinon, **failed**.
- Sans `status_code:`, le défaut est `[200]` — un 201 ferait failer la tâche.

**Autres `body_format:`** :

- **`json`** — sérialise dict → JSON.
- **`form-urlencoded`** — sérialise dict → `key=value&key2=value2`.
- **`raw`** — body brut, vous gérez la sérialisation.

## 📚 Exercice 3 — Authentification (Basic + Bearer)

```yaml
# Basic Auth (utilisateur/password)
- name: API privee avec Basic Auth
  ansible.builtin.uri:
    url: https://api.private.com/v1/resources
    method: GET
    url_username: "{{ vault_api_user }}"
    url_password: "{{ vault_api_password }}"
    force_basic_auth: true
    return_content: true
  register: api_resources

# Bearer Token (OAuth, JWT)
- name: API moderne avec Bearer token
  ansible.builtin.uri:
    url: https://api.github.com/user
    method: GET
    headers:
      Authorization: "Bearer {{ vault_github_token }}"
      Accept: "application/vnd.github+json"
    return_content: true
  register: github_user
```

🔍 **Observation** :

- **`force_basic_auth: true`** envoie l'en-tête `Authorization: Basic ...`
  **dès la première requête**. Sans ça, Ansible attend un 401 du serveur
  avant de re-tenter avec auth (souvent le bon comportement, mais coûte
  un round-trip).
- **`headers: Authorization: Bearer ...`** = le pattern OAuth/JWT moderne.
- **Secrets** : **toujours** dans Ansible Vault (`vault_*`).

## 📚 Exercice 4 — Healthcheck applicatif

Pattern classique : après déploiement d'une app, vérifier qu'elle répond.

```yaml
- name: Demarrer myapp
  ansible.builtin.systemd_service:
    name: myapp
    state: restarted

- name: Attendre que le port soit ouvert
  ansible.builtin.wait_for:
    port: 8080
    host: 127.0.0.1
    timeout: 30

- name: Verifier le healthcheck HTTP
  ansible.builtin.uri:
    url: http://localhost:8080/health
    method: GET
    status_code: 200
    return_content: true
  register: health
  until: health.json.status == "ok"
  retries: 5
  delay: 2

- name: Afficher la version deployee
  ansible.builtin.debug:
    msg: "myapp version : {{ health.json.version }}"
```

🔍 **Observation** : **`until: + retries: + delay:`** = polling. Ansible
relance la tâche **jusqu'à ce que** la condition soit vraie (max `retries`
fois, avec `delay` secondes entre chaque essai). Idéal pour des services qui
mettent quelques secondes à devenir disponibles.

## 📚 Exercice 5 — Upload de fichier (multipart)

```yaml
- name: Upload d un fichier de config
  ansible.builtin.uri:
    url: https://api.private.com/v1/configs
    method: POST
    src: /tmp/myapp.yml
    headers:
      Authorization: "Bearer {{ vault_token }}"
      Content-Type: "application/yaml"
    status_code: [200, 201]
```

🔍 **Observation** : **`src:`** envoie le **contenu du fichier** comme body
HTTP. Pour multipart/form-data, utiliser `body_format: form-multipart` (depuis
Ansible 2.10).

## 📚 Exercice 6 — `validate_certs: false` (DANGER)

```yaml
- name: API self-signed (DEV uniquement)
  ansible.builtin.uri:
    url: https://internal-dev.lab/api/info
    validate_certs: false
    return_content: true
```

🔍 **Observation** : désactive la vérification TLS — **risque MITM**. À
proscrire en prod (préférer ajouter le CA au truststore).

## 📚 Exercice 7 — `uri:` vs `get_url:`

| Cas | Module |
|---|---|
| Télécharger un fichier (binaire, archive) | **`get_url:`** |
| Télécharger un fichier avec checksum | **`get_url:`** |
| Appeler une API REST (GET, POST, PUT, DELETE) | **`uri:`** |
| Parser une réponse JSON | **`uri:` + `register.json`** |
| Healthcheck HTTP | **`uri:` + `until:`** |
| Upload de fichier vers API | **`uri:` + `src:`** |

🔍 **Observation** : `get_url:` est **optimisé pour le download de fichiers**
(idempotence par checksum, ETag, taille). `uri:` est **généraliste** pour
toute interaction HTTP, y compris des appels qui ne retournent pas de fichier.

## 🔍 Observations à noter

- **`uri:`** = appels HTTP REST (GET, POST, PUT, DELETE).
- **`return_content: true`** capture la réponse — JSON parsé automatiquement.
- **`status_code:`** liste les codes acceptés (défaut `[200]`).
- **`body_format: json`** sérialise un dict en JSON automatiquement.
- **Auth** : `url_username`/`url_password` (Basic) ou `headers:` (Bearer).
- **`until: + retries: + delay:`** = polling pour healthchecks.

## 🤔 Questions de réflexion

1. Vous appelez une API qui peut retourner `200` (OK) ou `404` (resource
   absente — pas une erreur métier). Comment configurer `uri:` pour que les
   deux soient acceptés sans `failed_when` ?

2. Différence entre `return_content: true` + capture de `register.json` vs
   `register.content | from_json` ? (indice : Content-Type).

3. Vous voulez **authentifier** une API avec un token qui change à chaque
   appel (rotated). Quel pattern (combinaison `uri:` x 2, `set_fact`,
   `headers:`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`creates:`** : skip l'appel si un fichier existe déjà côté managed node.
  Pattern d'idempotence pour les POST de ressources (ex : créer un user
  Grafana — on skip si on a déjà le marker).
- **`dest:`** : enregistre la réponse dans un fichier. Equivalent
  `get_url:` mais avec l'expressivité de `uri:` (POST + auth).
- **Pattern paginé** : combiner `until: not next_page` pour itérer sur des
  APIs paginées (`?page=N`).
- **Lab 49 (`get_url:`)** : pour les downloads simples.
- **`community.general.proxmox*`**, **`community.aws.*`** : modules
  spécialisés qui encapsulent `uri:` pour des APIs précises.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-reseau/uri/lab.yml
ansible-lint labs/modules-reseau/uri/challenge/solution.yml
ansible-lint --profile production labs/modules-reseau/uri/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
