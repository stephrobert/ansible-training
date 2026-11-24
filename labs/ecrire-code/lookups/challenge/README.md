# The token lives here, the server needs it there

## The situation

The API token sits in a file on the control node. **db1.lab** has never seen
it, and should never hold a copy of it beyond the config file you are about to
render. A colleague suggested copying the token onto db1 first and reading it
from there, which defeats the entire point of keeping it on one machine.
Ansible can read local data at template time and push only the result. That is
what lookups are for, and the direction is the whole lesson.

You work from **control-node.lab**.

Your mission:

1. Read the **API token from a file on the control node** and push it into
   `/tmp/lookups-challenge.txt` on `db1.lab`.
2. Add a value taken from the control node's **environment**, and one taken
   from the **output of a command** run locally.
3. Convince yourself of the direction: all three values describe your control
   node, not db1 — even though the file lands on db1.
4. Note that a file lookup resolves **relative to the playbook**, not to your
   shell, and know when `query` should replace `lookup`.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/lookups/ (in French)

## 🎯 Challenge — Combining 3 lookups

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, writes
`/tmp/lookups-challenge.txt` containing **3 values** read on the **control
node** (not on the managed node) via 3 different lookup plugins.

### 🧩 Preparation: create the source file

The `lookup('file', ...)` look for a file **on the control node** (relative
to the playbook directory). Prepare it:

```bash
mkdir -p labs/ecrire-code/lookups/challenge/files
echo "MAGIC-TOKEN-RHCE-2026" > labs/ecrire-code/lookups/challenge/files/api-token.txt
```

### 🧩 3 lookups to use

| Lookup | Role | Example |
| --- | --- | --- |
| `file` | Reads the content of a local file (control node) | `lookup('file', 'files/api-token.txt')` |
| `env` | Reads an environment variable of the control node | `lookup('env', 'HOME')` |
| `pipe` | Runs a shell command on the control node, returns stdout | `lookup('pipe', 'hostname -s')` |

> ⚠️ All the lookups run **on the control node**, **not** on the
> managed node, which is what makes them useful (pushing a local secret onto
> the remote hosts).

### 🧩 Expected output

`/tmp/lookups-challenge.txt` (on db1) must contain:

```text
token=MAGIC-TOKEN-RHCE-2026
home=/home/<you>
host_local=<short hostname of your machine>
```

### 🧩 Skeleton

```yaml
---
- name: Challenge - 3 lookups (file, env, pipe)
  hosts: ???
  become: ???

  tasks:
    - name: Poser /tmp/lookups-challenge.txt avec 3 lookups
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          token={{ lookup('???', '???') }}
          home={{ lookup('???', '???') }}
          host_local={{ lookup('???', '???') }}
```

> 💡 **Pitfalls**:
>
> - **On the control node**: the 3 lookups run **locally**, not
>   on `db1.lab`. When you read `lookup('env', 'HOME')`, you read
>   the home of **your machine**, not that of `student` on db1.lab.
> - **`lookup('file', ...)`**: path relative to the **playbook** (not the
>   CWD or the lab). In your case, `solution.yml` is in `challenge/`
>   so `lookup('file', 'files/api-token.txt')` looks for
>   `challenge/files/api-token.txt`.
> - **"input file not found" error**: if you forget to create
>   `files/api-token.txt`, the error occurs **at templating time**, not
>   in a pre-check. Double-check the `echo` command in the preparation.
> - **`lookup('pipe', '...')`**: the command runs via `/bin/sh -c`. No
>   shell variable expansion: pass a complete and simple
>   command (`hostname -s`, not `echo $USER`).

### 🚀 Run

```bash
ansible-playbook labs/ecrire-code/lookups/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lookups-challenge.txt"
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/lookups/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-lookups
```

### 💡 Going further

- **`lookup('vars', 'name')`**: retrieves the value of an Ansible variable by
  its name (useful in dynamic programming).
- **`lookup('first_found', [...])`**: returns the first file found in
  a list, a frequent pattern for OS-specific configs.
- **Difference `lookup` vs `query`**: `lookup` **always returns a
  string** (joined). `query` (or `q()`) returns a **list**. Prefer
  `query` when you handle several values.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/lookups/challenge/solution.yml
   ```
