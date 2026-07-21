# 🎯 Challenge — Module `uri:` (API calls + JSON parsing)

## ✅ Objective

On **db1.lab**, make 2 HTTP calls with **`ansible.builtin.uri`** to the internal
inventory API of the lab, served by **`api-interne.lab:8009`**:

| # | URL | Method | Specificity |
| --- | --- | --- | --- |
| 1 | `http://api-interne.lab:8009/api/reference` | GET | Captures JSON, writes to `/opt/lab-uri-get.json` |
| 2 | `http://api-interne.lab:8009/api/noeuds` | POST | JSON body `{name: rhce, version: 2026}`, writes the response to `/opt/lab-uri-post.json` |

No `command: curl`. Everything through the Ansible module.

> 🔎 **The API runs in the lab, not on the Internet.** `setup.yaml` sets it up
> (nginx on web2.lab) and publishes the name `api-interne.lab` in the
> `/etc/hosts` of db1. The lab therefore needs no outbound access. The server
> **logs every call**: the tests re-read this log, and therefore see whether
> the request really went out, and with which agent.

## 🧩 Steps

1. **GET** `http://api-interne.lab:8009/api/reference`:
   - `return_content: true` to capture the body.
   - `register: get_response`.
   - **Write** `get_response.content` to `/opt/lab-uri-get.json` via `copy:
     content:`.
2. **POST** `http://api-interne.lab:8009/api/noeuds` with body
   `{name: rhce, version: 2026}`:
   - `body_format: json`, `body:` a YAML dict.
   - **`status_code: [200, 201]`**: the API answers **201 (Created)**. The
     module default is `[200]`: without this line, the task **fails**.
   - `register: post_response`.
   - **Write** `post_response.json | to_nice_json` to `/opt/lab-uri-post.json`.

## 🧩 Skeleton

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

> 💡 **Traps**:
>
> - **`return_content: true`** (default `false`): captures the body of the
>   response in `<var>.content`. Without it, you only have the HTTP code +
>   headers.
> - **`status_code:`** = list of accepted codes. By default `[200]`. The API of
>   this lab answers **201** on the POST: `status_code: [200, 201]` is not
>   decorative, it is what makes the task pass.
> - **`body_format: json`**: serializes the `body:` into JSON automatically and
>   sets `Content-Type: application/json`. Without it, the `body:` is treated
>   as a string.
> - **The responses of this API are deterministic**: two calls return exactly
>   the same bytes. You can therefore write the entire response without
>   breaking idempotence. Facing a real public API, beware: a trace identifier
>   or a timestamp in the response would make the `copy:` `changed` on every
>   pass.

## 🚀 Launch

```bash
ansible-playbook labs/modules-reseau/uri/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-uri-*.json"
ansible db1.lab -m ansible.builtin.command -a "head -5 /opt/lab-uri-get.json"
# Did the server see your calls go by?
ansible web2.lab -b -m ansible.builtin.command -a "cat /var/log/nginx/lab-uri-api.log"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-reseau/uri/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/opt/lab-uri-get.json state=absent"
ansible db1.lab -b -m file -a "path=/opt/lab-uri-post.json state=absent"
```

## 💡 Going further

- **`until:` + `retries:` + `delay:`**: application healthcheck, repeat the
  call until it responds correctly (at most N times).
- **Authentication**: `url_username` / `url_password` (Basic) or
  `headers: Authorization: Bearer ...` (OAuth/JWT). The `get-url` lab
  demonstrates it on a protected internal repo.
- **`creates:`**: skip the call if a file already exists on the managed node
  (idempotence for creation POSTs).
- **`dest:`**: saves the response into a file (equivalent to `register:` +
  `copy: content:`).
- **Lint**:

   ```bash
   ansible-lint labs/modules-reseau/uri/challenge/solution.yml
   ```
