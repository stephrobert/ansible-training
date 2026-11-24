# Harden the app config without touching the neighbours

## The situation

The application on **db1.lab** reads `/etc/myapp.conf`, and three changes
landed at once: the API moved to a new domain behind TLS, the service port
switched to 8443, and SSL must be turned on. The trap is written into the
file itself: it stacks a `[server]` and a `[client]` section, and both
declare `ssl_enabled=false`. Only the server side must flip to `true`; a
blind substitution would also flip the client and break its handshake. You
operate from **control-node.lab**, on a file that must come out surgically
edited.

Your mission:

1. Move the API URL to **https on its new domain**, everywhere it appears,
   keeping the path intact.
2. Bump the **port to 8443** while preserving the `port=` prefix, rather
   than rewriting the whole line.
3. Enable SSL **in the `[server]` section only**, by **bounding the
   substitution zone** rather than trusting the pattern.
4. Prove the collateral damage is nil: `[client]` still says
   `ssl_enabled=false`, and a second run reports no change.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/ (in French)

## Challenge `replace:`

### Brief

The lab setup placed the following `/etc/myapp.conf` file on **db1.lab**:

```ini
url=http://api-old.example.com/v1
port=8080
[server]
ssl_enabled=false
host=localhost
[client]
ssl_enabled=false
host=localhost
```

Write `solution.yml` that transforms this file to reach exactly this state:

```ini
url=https://api.example.com/v1
port=8443
[server]
ssl_enabled = true
host=localhost
[client]
ssl_enabled=false
host=localhost
```

In other words:

1. The API URL switches to **https** on the new domain
   `api.example.com` (the `/v1` path is preserved).
2. The port changes from 8080 to **8443**, keeping the `port=` prefix.
3. `ssl_enabled` changes to `true` (with spaces: `ssl_enabled = true`)
   **only in the `[server]` section**: the `[client]` section
   keeps `ssl_enabled=false` identical.
4. A 2nd run of the playbook changes nothing (idempotent).

### Success criteria

- `grep https://api.example.com /etc/myapp.conf` matches, and
  `api-old.example.com` has disappeared.
- `grep port=8443 /etc/myapp.conf` matches, and `port=8080` has disappeared.
- Between `[server]` and `[client]`: `ssl_enabled = true`.
- After `[client]`: still `ssl_enabled=false`.
- 1st run: `changed`. 2nd run: `ok` (idempotent).

### 🧩 Stuck?

```bash
dsoxlab hint modules-fichiers-replace
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
