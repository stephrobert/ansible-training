# Lab 50 — Module `uri:` (REST API calls)

## 🧠 Recap

🔗 [**Ansible uri module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-uri/)

`ansible.builtin.uri:` makes **HTTP/HTTPS** calls from the managed node:
GET, POST, PUT, DELETE. It is the equivalent of a `curl` but with **explicit
idempotence**, **automatic JSON** parsing, and structured **error handling**.

RHCE 2026 use cases: application healthchecks, **resource creation** via API
(Kubernetes, Vault, Grafana), **OAuth token retrieval**, webhook notifications
(Slack, Teams).

Critical options: **`url:`**, **`method:`** (GET by default), **`status_code:`**
(list of accepted codes), **`return_content: true`** (captures the response),
**`body:`** + **`body_format:`** (json/form-urlencoded/raw), **`headers:`**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Do a simple GET** and capture the response (`return_content: true`).
2. **Do a POST** with a JSON body (`body_format: json`).
3. **Authenticate** via `url_username`/`url_password` (Basic) or `headers:`
   (Bearer).
4. **Accept several return codes** (`status_code: [200, 201, 204]`).
5. **Distinguish** `uri:` (REST API) from `get_url:` (file download).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — Simple GET + response capture

> 🔎 **The API of this lab runs in the lab.** `api-interne.lab:8009` is served
> by nginx from web2.lab, set up by the `setup.yaml`. No Internet access is
> required: this lab used to hit `httpbin.org`, which returned 503s and
> responses at 26 seconds, and made it fail for a reason completely unrelated
> to the `uri` module.

```yaml
---
- name: Demo uri GET
  hosts: db1.lab
  tasks:
    - name: Recuperer la charge utile de reference
      ansible.builtin.uri:
        url: http://api-interne.lab:8009/api/reference
        method: GET
        return_content: true
      register: api_response

    - name: Afficher la version (parsing JSON automatique)
      ansible.builtin.debug:
        msg: "Version de l API : {{ api_response.json.version }}"

    - name: Afficher quelques champs
      ansible.builtin.debug:
        msg: |
          api : {{ api_response.json.api }}
          environnements : {{ api_response.json.environnements | join(', ') }}
          noeuds : {{ api_response.json.noeuds_declares }}
```

🔍 **Observation**:

- **`return_content: true`** captures the response in `register.content` (raw)
  AND `register.json` (parsed if `Content-Type: application/json`).
- **No need for `from_json`**, Ansible parses JSON responses automatically.
- **`method: GET`** is the default, you can omit it.

## 📚 Exercise 2 — POST with a JSON body

```yaml
- name: Creer une ressource via POST
  ansible.builtin.uri:
    url: http://api-interne.lab:8009/api/noeuds
    method: POST
    body_format: json
    body:
      name: "myapp"
      version: "1.0.0"
      env: "prod"
    status_code: [200, 201]
    return_content: true
  register: post_result

- name: Afficher l accuse de creation rendu par l API
  ansible.builtin.debug:
    msg: "Serveur : {{ post_result.json.statut }} -> {{ post_result.json.ressource }}"
```

🔍 **Observation**:

- **`body_format: json`** automatically serializes the Ansible dict into JSON
  for the HTTP body.
- **`status_code: [200, 201]`**: the task **succeeds** if the server returns
  200 OR 201. Otherwise, **failed**.
- Without `status_code:`, the default is `[200]`, and a 201 would fail the
  task. **This API answers exactly 201**: remove the line and watch the task
  fail. It is the only way to remember the rule.

**Other `body_format:`**:

- **`json`**, serializes dict → JSON.
- **`form-urlencoded`**, serializes dict → `key=value&key2=value2`.
- **`raw`**, raw body, you handle the serialization.

## 📚 Exercise 3 — Authentication (Basic + Bearer)

```yaml
# Basic Auth (user/password)
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

🔍 **Observation**:

- **`force_basic_auth: true`** sends the `Authorization: Basic ...` header
  **from the first request**. Without it, Ansible waits for a 401 from the
  server before retrying with auth (often the right behavior, but costs a
  round-trip).
- **`headers: Authorization: Bearer ...`** = the modern OAuth/JWT pattern.
- **Secrets**: **always** in Ansible Vault (`vault_*`).

## 📚 Exercise 4 — Application healthcheck

Classic pattern: after deploying an app, check that it responds.

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

🔍 **Observation**: **`until: + retries: + delay:`** = polling. Ansible reruns
the task **until** the condition is true (at most `retries` times, with `delay`
seconds between each attempt). Ideal for services that take a few seconds to
become available.

## 📚 Exercise 5 — File upload (multipart)

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

🔍 **Observation**: **`src:`** sends the **content of the file** as the HTTP
body. For multipart/form-data, use `body_format: form-multipart` (since Ansible
2.10).

## 📚 Exercise 6 — `validate_certs: false` (DANGER)

```yaml
- name: API self-signed (DEV uniquement)
  ansible.builtin.uri:
    url: https://internal-dev.lab/api/info
    validate_certs: false
    return_content: true
```

🔍 **Observation**: disables the TLS verification, **MITM risk**. To be banned
in prod (prefer adding the CA to the truststore).

## 📚 Exercise 7 — `uri:` vs `get_url:`

| Case | Module |
|---|---|
| Download a file (binary, archive) | **`get_url:`** |
| Download a file with checksum | **`get_url:`** |
| Call a REST API (GET, POST, PUT, DELETE) | **`uri:`** |
| Parse a JSON response | **`uri:` + `register.json`** |
| HTTP healthcheck | **`uri:` + `until:`** |
| File upload to an API | **`uri:` + `src:`** |

🔍 **Observation**: `get_url:` is **optimized for file downloads** (idempotence
by checksum, ETag, size). `uri:` is **general-purpose** for any HTTP
interaction, including calls that do not return a file.

## 🔍 Observations to note

- **`uri:`** = REST HTTP calls (GET, POST, PUT, DELETE).
- **`return_content: true`** captures the response, JSON parsed automatically.
- **`status_code:`** lists the accepted codes (default `[200]`).
- **`body_format: json`** serializes a dict into JSON automatically.
- **Auth**: `url_username`/`url_password` (Basic) or `headers:` (Bearer).
- **`until: + retries: + delay:`** = polling for healthchecks.

## 🤔 Reflection questions

1. You call an API that can return `200` (OK) or `404` (resource absent, not a
   business error). How do you configure `uri:` so that both are accepted
   without `failed_when`?

2. Difference between `return_content: true` + capture of `register.json` vs
   `register.content | from_json`? (hint: Content-Type).

3. You want to **authenticate** an API with a token that changes on every call
   (rotated). Which pattern (combination of `uri:` x 2, `set_fact`,
   `headers:`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`creates:`**: skip the call if a file already exists on the managed node.
  Idempotence pattern for resource POSTs (for example creating a Grafana user,
  we skip if we already have the marker).
- **`dest:`**: saves the response into a file. Equivalent to `get_url:` but with
  the expressiveness of `uri:` (POST + auth).
- **Paginated pattern**: combine `until: not next_page` to iterate over
  paginated APIs (`?page=N`).
- **Lab 49 (`get_url:`)**: for simple downloads.
- **`community.general.proxmox*`**, **`community.aws.*`**: specialized modules
  that wrap `uri:` for specific APIs.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-reseau/uri/lab.yml
ansible-lint labs/modules-reseau/uri/challenge/solution.yml
ansible-lint --profile production labs/modules-reseau/uri/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
