# 🎯 Challenge — Override variables at play level

You have seen the `webserver` role parameterized by `defaults/main.yml`. The challenge is to **override** these values from a playbook that calls the role, and to **prove** that the new values are indeed applied.

## ✅ Objective

Write `solution.yml` that:

1. Targets **`db1.lab`** only.
2. Calls the `webserver` role with **3 overridden variables**:
   - `webserver_listen_port: 8080` (instead of 80)
   - `webserver_worker_connections: 2048` (instead of 1024)
   - `webserver_index_content: "Custom page from challenge lab 59 on {{ inventory_hostname }}"`

## 🧩 Instructions

Skeleton to complete (`challenge/solution.yml`):

```yaml
---
- name: Challenge — override des defaults d'un rôle au niveau du play
  hosts: ???
  become: ???
  roles:
    - role: webserver
      vars:                              # play vars: priority 12
        webserver_listen_port: ???       # 8080
        webserver_worker_connections: ???    # 2048
        webserver_index_content: "{{ ??? }}"   # with inventory_hostname
```

Run (note the env var `ANSIBLE_ROLES_PATH`, not `-e`):

```bash
ANSIBLE_ROLES_PATH=labs/roles/variables-defaults-vars/roles \
ansible-playbook labs/roles/variables-defaults-vars/challenge/solution.yml
```

> 💡 **Pitfalls**:
>
> - **Precedence**: the role's `vars/` (priority 15) > the play's `vars:`
>   (priority 12) > the role's `defaults/` (priority 2). If you try
>   to override `__webserver_html_dir` (defined in `vars/main.yml`), it
>   **does not work**. To override, modify the role or use
>   `--extra-vars` (priority 22, the very top).
> - **`ANSIBLE_ROLES_PATH`** is an Ansible env var, **not a `-e`** of the
>   playbook. The `-e ansible_roles_path=...` configures nothing (it is an
>   extra-var useless to the play).
> - **Variables with `inventory_hostname`**: remember to put them in
>   quotes because `{{ }}` can be interpreted by YAML (`"{{ ... }}"`).

Check on `db1.lab`:

   ```bash
   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "sudo firewall-cmd --zone=public --list-ports"
   # → 8080/tcp must appear

   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "cat /usr/share/nginx/html/index.html"
   # → Custom page from challenge lab 59 on db1.lab
   ```

## 🧪 Validation

The pytest test automatically checks:

- nginx installed.
- nginx service running.
- Firewalld has port **8080/tcp** open (proof that `webserver_listen_port=8080` was passed via the play's `vars:`, **not** the value 80 from `defaults/`).
- The file `/usr/share/nginx/html/index.html` contains the **custom message**.

```bash
pytest -v challenge/tests/
```

## 🚀 Going further

- Modify the role's `defaults/main.yml` to set `webserver_listen_port: 80` (already the default value). Re-run the solution. The result is the **same**: proof that **the play's `vars:` override the `defaults/`**.
- Try to override `__webserver_html_dir` (which is in `vars/main.yml`). Observe that the override value **is not taken into account**: `vars/` (priority 15) wins over the play's `vars:` (priority 12). Caution: a `vars:` placed under `- role:` is a role param (priority 20), and it WINS.
- Combine `--extra-vars "webserver_listen_port=9999"` on the CLI: this value **wins over everything** (priority 22, the top of the precedence).

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean roles-variables-defaults-vars
```

This target uninstalls/removes what the solution set up on the managed
nodes (packages, files, services, firewall rules) so that you can
re-run the solution from scratch.
