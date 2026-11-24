# Four transformations nobody should do by hand

## The situation

The integration you are wiring needs four things Ansible will not hand you
ready-made: the machine's role prefix, buried inside its FQDN; a Basic auth
header, which means the credentials pair must be base64 encoded; a list that
arrives nested from another team's export; and a sha256 fingerprint so you can
tell whether a payload actually changed. All four are done by hand today, from
a wiki page of copy-pasteable commands, and the wiki page is wrong.

You do them in the data, on `db1.lab`, from **control-node.lab**.

Your mission:

1. **Extract** the role prefix from an FQDN with a regex, anchored so it stops
   before the first digit.
2. **Encode** the credentials pair to base64, and stay clear about what that
   is: encoding, never encryption.
3. **Flatten** the nested list into a flat one, and check how deep the filter
   goes before it gives up.
4. Produce a **sha256** fingerprint of a string, then write the four results on
   db1.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/filtres-jinja/ (in French)

## 🎯 Challenge — 4 advanced Jinja2 filters

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, writes
`/tmp/filtres-avances.txt` containing **4 lines**, each produced by an
advanced Jinja2 filter.

### 🧩 Input data

```yaml
fqdn: "web1.lab.example.com"
secret: "admin:secret"
nested: [[1, 2], [3, [4, 5]]]
to_hash: "foobar"
```

### 🧩 Expected output

```text
prefix=web
b64=YWRtaW46c2VjcmV0
flat=[1, 2, 3, 4, 5]
sha256=c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2
```

### 🧩 4 filters to use

| Filter | Effect |
| --- | --- |
| `regex_search('pattern')` | Returns the 1st substring that matches the pattern |
| `b64encode` | Encodes to Base64 (useful for `Authorization: Basic`) |
| `flatten` | Recursively flattens a list of lists |
| `hash('sha256')` | Hexadecimal SHA256 fingerprint of a string |

### 🧩 Skeleton

```yaml
---
- name: Challenge - 4 filtres avancés
  hosts: db1.lab
  become: true

  vars:
    fqdn: "web1.lab.example.com"
    secret: "admin:secret"
    nested: [[1, 2], [3, [4, 5]]]
    to_hash: "foobar"

  tasks:
    - name: Poser /tmp/filtres-avances.txt
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          prefix={{ fqdn | regex_search(???) }}
          b64={{ secret | ??? }}
          flat={{ nested | ??? }}
          sha256={{ to_hash | ???(???) }}
```

> 💡 **Regex hint**: to extract **only** the `web` prefix from
> `web1.lab.example.com`, use the pattern `^([a-z]+)` (anchored at the start,
> captures only lowercase letters).

**Pitfalls**:

> - **`regex_search` returns `None`** if there is no match; use `default(...)`
>   for a fallback. `regex_findall` returns a list (empty if no
>   match).
> - **`b64encode`**: the output stays a **string** (not bytes). To decode,
>   `b64decode`. Important: this is **not encryption** (just
>   encoding).
> - **`flatten`**: flattens a list of lists. Default depth level
>   = 1. To flatten completely, `flatten(levels=99)`.
> - **`hash`** filter: SHA1 by default. For SHA256:
>   `to_hash | hash('sha256')`. For MD5: `'md5'`. **Never**
>   use `hash` on a secret: it is a hash, not an auth.

### 🚀 Run

```bash
ansible-playbook labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/filtres-avances.txt"
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/filtres-jinja-avances/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-filtres-jinja-avances
```

### 💡 Going further

- **`hash('md5')` / `hash('sha1')` / `hash('sha512')`**: other algorithms. On
  recent Ansible versions, `password_hash('sha512')` generates a
  `/etc/shadow`-style password hash.
- **`b64decode`**: decodes Base64 (typically to read a secret coming
  from a Vault/Kubernetes Secret).
- **`from_yaml` / `from_json`**: parse a YAML/JSON string into a dict.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
   ```
