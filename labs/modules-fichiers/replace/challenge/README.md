# Challenge `replace:`

## Brief

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

## Success criteria

- `grep https://api.example.com /etc/myapp.conf` matches, and
  `api-old.example.com` has disappeared.
- `grep port=8443 /etc/myapp.conf` matches, and `port=8080` has disappeared.
- Between `[server]` and `[client]`: `ssl_enabled = true`.
- After `[client]`: still `ssl_enabled=false`.
- 1st run: `changed`. 2nd run: `ok` (idempotent).

## 🧩 Stuck?

```bash
dsoxlab hint modules-fichiers-replace
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
