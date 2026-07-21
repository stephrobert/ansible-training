# 🎯 Challenge — Module `get_url:` (download with checksum)

## ✅ Objective

On **db1.lab**, download 2 files from the **internal reference repository** of
the lab, served by `depot-interne.lab:8008`, with **integrity check** (sha256),
**authentication**, strict permissions and guaranteed idempotence.

| Task | URL | Destination | Specificity |
| --- | --- | --- | --- |
| Public text | `http://depot-interne.lab:8008/depot/gpl-3.0.txt` | `/opt/lab-gpl3.txt` | Mode 0644 + `checksum:` sha256 |
| Protected text | `http://depot-interne.lab:8008/prive/lgpl-3.0.txt` | `/opt/lab-lgpl3.txt` | Mode 0644 + `force: false` + **Basic Auth** |

Use **`ansible.builtin.get_url`**. No `command: curl` and no `command: wget`.

> 🔎 **The repo runs in the lab, not on the Internet.** `setup.yaml` sets it up
> (nginx on web2.lab) and publishes the name `depot-interne.lab` in the
> `/etc/hosts` of db1. The lab needs no outbound access. The server **logs
> every request**: the tests re-read this log and therefore see whether you
> really checked the integrity, and with which agent you downloaded.

### 🔑 Access to the protected zone

| User | Password |
| --- | --- |
| `depot` | `rhce2026` |

The password is in cleartext here because the subject of this lab is `get_url`.
In production it would live in **Ansible Vault**: that is the subject of the
"vault" section of the training.

## 🧩 Steps

1. **Download** `gpl-3.0.txt` to `/opt/lab-gpl3.txt` (mode 0644), **checking
   its sha256 fingerprint**. The repo publishes the sums next to the file, at
   `http://depot-interne.lab:8008/depot/gpl-3.0.txt.sha256`: point to it with
   `checksum: sha256:<url>`, do not copy a fingerprint by hand. This is how a
   serious mirror works, and it is what keeps the playbook correct even when
   the upstream file changes version.
2. **Download** `lgpl-3.0.txt` to `/opt/lab-lgpl3.txt` (mode 0644) from the
   protected zone: without credentials, the server returns **401** and the task
   fails. Add `force: false` (do not re-download if present).
3. **Check** that a 2nd run of the playbook does **not** re-download
   (idempotence).

## 🧩 Skeleton

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

> 💡 **Traps**:
>
> - **`force: false`** (default): if `dest` exists, does not re-download.
>   Idempotent. With `force: true`, re-downloads on every run.
> - **`checksum:`**: format `algo:hash` (for example `sha256:abc123…`) **or
>   `algo:url`** (for example `sha256:http://…/fichier.sha256`), and it is this
>   second form we want here. If the fingerprint does not match → task failed
>   AND file removed. Supply-chain security: a compromised mirror does not get
>   through.
> - **`force_basic_auth: true`**: sends the `Authorization` header from the
>   first request. Without it, Ansible waits for the server's 401 before
>   retrying with the credentials: that works too, but costs a round trip.
> - **`validate_certs:`**: `true` by default. The lab repo is plain HTTP, the
>   question does not arise here; facing a self-signed cert in dev: `false`
>   (anti-pattern in prod).
> - **Corporate proxy**: `environment: { http_proxy: '...', https_proxy: '...' }`
>   at the task or play level.

## 🚀 Launch

```bash
ansible-playbook labs/modules-reseau/get-url/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
ansible db1.lab -m ansible.builtin.command -a "wc -l /opt/lab-gpl3.txt /opt/lab-lgpl3.txt"
# Did the repo see your requests go by?
ansible web2.lab -b -m ansible.builtin.command -a "cat /var/log/nginx/lab-get-url-depot.log"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-reseau/get-url/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/opt/lab-gpl3.txt state=absent"
ansible db1.lab -b -m file -a "path=/opt/lab-lgpl3.txt state=absent"
```

## 💡 Going further

- **`headers:`**: injection of Bearer tokens / API keys for authenticated
  endpoints. Store the secrets in **Ansible Vault**.
- **`validate_certs: false`**: disables the TLS check. To be **banned** in
  prod, prefer adding the root CA to the truststore.
- **`get_url:` + `unarchive:`**: classic chaining to download + extract an
  upstream release (with `creates:` for idempotence).
- **`uri:`**: to call a REST API rather than download a file. That is the
  subject of the next lab.
- **Lint**:

   ```bash
   ansible-lint labs/modules-reseau/get-url/challenge/solution.yml
   ```
