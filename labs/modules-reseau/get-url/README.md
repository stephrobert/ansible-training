# Lab 49 — Module `get_url:` (download an HTTP/HTTPS file)

## 🧠 Recap

🔗 [**Ansible get_url module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-get-url/)

`ansible.builtin.get_url:` downloads a file from an HTTP/HTTPS/FTP URL
**directly onto the managed node** (no round trip through the control node).
It is the number 1 RHCE 2026 module to fetch an upstream binary, an
**application release**, a custom **RPM repository**, or an external config
file.

Critical options: **`url:`**, **`dest:`**, **`mode:`**, **`checksum:`**
(integrity check), **`force: true`** (override), **`headers:`**
(API authentication), **`validate_certs:`** (strict TLS).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Download** a file with `get_url:` (idempotent by default).
2. **Check the integrity** with `checksum: sha256:...`.
3. **Authenticate** a download with `url_username:` / `url_password:` or
   `headers:`.
4. **Disable strict TLS** with `validate_certs: false` (not recommended in prod).
5. **Choose** between `get_url:` (simple download) and `uri:` (JSON API call).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /opt/lab-download-* /tmp/lab-get-*"
```

## 📚 Exercise 1 — Basic download

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

🔍 **Observation**:

- 1st run: `changed=1`, file downloaded.
- 2nd run: `changed=0`, Ansible checks the **ETag** or the HTTP **modification
  date**. If the server has not changed, no re-download.

**Idempotence by default**: `get_url` re-downloads **only if necessary**.
Handy for versioned artifacts where the URL already contains the version
(`myapp-1.0.0.tar.gz`).

## 📚 Exercise 2 — Integrity check (`checksum:`)

```yaml
- name: Telecharger node_exporter avec verification SHA256
  ansible.builtin.get_url:
    url: https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
    dest: /opt/node_exporter.tar.gz
    checksum: sha256:a550cd5c05f760b7934a2d0afad66d2e92e681482f5f57a917465b1fba3b02a6
    mode: "0644"
```

🔍 **Observation**:

- If the downloaded file has a SHA256 **different** from the one specified, the
  task is **failed**.
- If **identical**, idempotent, no re-download.

**Supported formats**:

- **`sha256:<hex>`**, recommended (collision-resistant).
- **`sha512:<hex>`**, stronger (generally overkill).
- **`sha1:<hex>`**, deprecated for security.
- **`md5:<hex>`**, do **not** use (cryptographically broken).
- **`sha256:https://example.com/SHA256SUMS`**, fetches the list of sums from a
  URL and matches the filename.

**Production pattern**: **always** specify a checksum for critical binaries.
Without it, a MITM or a compromised repo could push anything.

## 📚 Exercise 3 — Authentication

```yaml
# Basic authentication (HTTP Basic)
- ansible.builtin.get_url:
    url: https://repo.private.com/files/private.tar.gz
    dest: /opt/private.tar.gz
    url_username: "{{ vault_repo_user }}"
    url_password: "{{ vault_repo_password }}"
    mode: "0600"

# Bearer token (modern API)
- ansible.builtin.get_url:
    url: https://api.github.com/repos/myorg/myapp/releases/latest
    dest: /opt/release-meta.json
    headers:
      Authorization: "Bearer {{ vault_github_token }}"
      Accept: application/vnd.github+json
    mode: "0600"
```

🔍 **Observation**:

- **`url_username` / `url_password`**: HTTP Basic Auth.
- **`headers:`**: for Bearer tokens, custom API keys, User-Agent.
- **`mode: "0600"`** on files containing auth content (license, token).

**Storage of secrets**: **always** in Ansible Vault (`vault_*` by convention),
never hardcoded in the playbook.

## 📚 Exercise 4 — `force: true` (override)

```yaml
- name: Forcer le re-download meme si checksum match
  ansible.builtin.get_url:
    url: https://example.com/dynamic-content.txt
    dest: /opt/lab-download-dynamic.txt
    force: true
    mode: "0644"
```

🔍 **Observation**: by default, `get_url` is idempotent, it does **not**
re-download if the file already exists with the right content. **`force: true`**
forces the download on every run.

**Use cases**:

- Endpoint that returns **dynamic** content (CSRF token, hourly snapshot).
- Re-download to **rotate** an artifact (for example a new TLS cert).

## 📚 Exercise 5 — `validate_certs:` (strict TLS)

```yaml
- name: Telecharger depuis un certif self-signed (DEV uniquement)
  ansible.builtin.get_url:
    url: https://internal-dev.lab/file.tar.gz
    dest: /opt/file.tar.gz
    validate_certs: false   # DISABLES THE TLS CHECK - DANGER
    mode: "0644"
```

🔍 **Observation**: `validate_certs: false` disables the verification of the
TLS certificate. **MITM risk**.

**Legitimate cases**:

- Internal lab with self-signed PKI (but prefer adding the root CA to the truststore).
- Temporary test on a dev environment.

**Never in prod**: if you see `validate_certs: false` in production code, it is
a **security flaw**, fix the truststore or use a valid cert (Let's Encrypt,
internal CA).

## 📚 Exercise 6 — Combine with `unarchive:`

Frequent pattern: download a tarball + extract it in one chain.

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

🔍 **Observation**: a more direct alternative, `unarchive: src:` accepts URLs
directly with `remote_src: true`. But no `checksum:` on the `unarchive:` side,
so if integrity matters, do `get_url:` then `unarchive:` separately.

## 📚 Exercise 7 — The trap: a changing `url:` vs identical content

```yaml
# The query string changes on every run, but the server content is identical
- ansible.builtin.get_url:
    url: "https://example.com/static.zip?cache_buster={{ ansible_date_time.epoch }}"
    dest: /opt/lab-download-static.zip
```

🔍 **Observation**: if the URL changes on every run (timestamp, token), Ansible
does **not** know that the content is identical → **re-download on every run**.

**Mitigation**: use `checksum:` on the **content**:

```yaml
- ansible.builtin.get_url:
    url: "https://example.com/static.zip?cache_buster={{ ansible_date_time.epoch }}"
    dest: /opt/lab-download-static.zip
    checksum: sha256:abc123...
```

With a checksum, Ansible compares the **local content** to the expected
checksum, and if it matches, **skips** even if the URL differs.

## 🔍 Observations to note

- **`get_url:`** downloads **on the managed node side** (not via the control node).
- **Idempotent by default** via HTTP ETag / Last-Modified.
- **`checksum: sha256:...`** for the integrity check (mandatory in prod).
- **`headers:`** for Bearer tokens and API keys.
- **`validate_certs: false`** = DANGER, only in dev with an internal PKI.
- **Dynamic URL** (timestamp, token) → use `checksum:` for idempotence.

## 🤔 Reflection questions

1. You download `myapp-1.0.0.tar.gz` (stable URL) then `myapp-1.1.0.tar.gz`
   (different URL). How do you **keep the history** of the two versions on the
   managed node, and switch between them?

2. Why is `checksum: sha256:...` **safer** than comparing HTTP
   `Content-Length`? Give 2 reasons.

3. `get_url:` downloads a 5GB file. The connection drops at 4GB. What is the
   default behavior on the next run?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`tmp_dest:`**: temporary download folder (useful if `/tmp` is small or on
  tmpfs).
- **`backup: true`**: create a backup of the previous file before overwrite.
- **`timeout:`**: HTTP timeout in seconds (default 10).
- **Repo mirroring**: combination `get_url:` + `loop:` to synchronize N files
  from a repo, idempotent.
- **Lab 50 (`uri:`)**: for **REST API** calls rather than file downloads.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-reseau/get-url/lab.yml
ansible-lint labs/modules-reseau/get-url/challenge/solution.yml
ansible-lint --profile production labs/modules-reseau/get-url/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
