# 🎯 Challenge — Write your own role and deploy it on db1.lab

You deployed the `webserver` role on `web1.lab`, but that role was **provided ready-made**. The challenge is to **create a role yourself** named `nginx-server` on the same structural model, and to deploy it on `db1.lab`.

The goal: practice **creating a role from scratch**, from `ansible-galaxy role init` all the way to calling it from a playbook. The deployed software does not change: the role structure is the subject.

## ✅ Objective

Write `solution.yml` that:

1. Targets **`db1.lab`** only.
2. Calls an `nginx-server` role **that you will create** with:
   - `roles/nginx-server/tasks/main.yml` that installs **nginx**, starts it, opens HTTP in firewalld
   - `roles/nginx-server/defaults/main.yml` with at least `nginx_state: present`
   - `roles/nginx-server/handlers/main.yml` with `Restart nginx`
   - `roles/nginx-server/meta/main.yml` minimal (galaxy_info)
   - `roles/nginx-server/README.md` minimal

## 🧩 Instructions

### 1. Create the role structure

```bash
cd labs/roles/creer-premier-role/
ansible-galaxy role init challenge/roles/nginx-server
ls challenge/roles/nginx-server/      # 9 sub-directories generated (tasks, defaults, handlers, meta…)
```

### 2. Complete `tasks/main.yml`

```yaml
---
- name: Installer nginx
  ansible.builtin.dnf:
    name: ???
    state: ???

- name: Démarrer + activer nginx
  ansible.builtin.systemd_service:
    name: ???
    state: ???
    enabled: ???

- name: Ouvrir HTTP dans firewalld (persistant + immédiat)
  ansible.posix.firewalld:
    service: ???                  # standard service (not a hard-coded port)
    permanent: ???
    immediate: ???
    state: ???
```

### 3. Complete `defaults/main.yml`

```yaml
---
nginx_state: ???                   # package 'present' by default
```

### 4. Complete `handlers/main.yml`

```yaml
---
- name: Restart nginx
  ansible.builtin.systemd_service:
    name: nginx
    state: ???                     # restarted
```

### 5. Write `solution.yml` (skeleton to complete)

```yaml
---
- name: "Challenge : déployer nginx via un rôle"
  hosts: ???
  become: ???
  roles:
    - role: ???                    # name of the directory under challenge/roles/
```

### 6. Run from the repo root

```bash
ANSIBLE_ROLES_PATH=labs/roles/creer-premier-role/challenge/roles \
ansible-playbook \
    -i labs/roles/creer-premier-role/inventory/hosts.yml \
    labs/roles/creer-premier-role/challenge/solution.yml
```

> 💡 **Pitfalls**:
>
> - **`ANSIBLE_ROLES_PATH`** is an Ansible **environment variable**,
>   not an Ansible `-e` (which sets play extra-vars, not configs).
>   Do not confuse them.
> - **Idempotence** of the role: `state: started` (and not `restarted`) in
>   `tasks/`. The `restarted` only goes in `handlers/` (triggered
>   conditionally by a `notify`).
> - **`firewalld`**: `service: http` rather than `port: 80/tcp`. It is
>   more readable and more portable (the service is defined in
>   `/usr/lib/firewalld/services/`).
> - **`ansible-galaxy role init`** creates 9 sub-directories, you do not
>   need to fill all of them. `defaults/`, `tasks/`, `handlers/`, `meta/`
>   are enough here.

### 7. Test

   ```bash
   curl http://db1.lab/
   ```

   Expected output: nginx's default welcome page.

## 🧪 Validation

The pytest test automatically checks:

- The `nginx` package is installed on `db1.lab`.
- The `nginx` service is `running` and `enabled`.
- Port 80 is open in firewalld.
- An HTTP request `http://db1.lab/` returns **200**.

```bash
pytest -v challenge/tests/
```

## 🚀 Going further

- Refactor the role so that it accepts an `nginx_listen_port` parameter and templates `nginx.conf` accordingly. Caution: a non-standard port requires an SELinux label. This is the subject of **lab 59** (variables).
- Compare the `ansible-playbook` outputs with `--check --diff` before the real run.
- Extend the role to also install `php-fpm` as a dependency, the subject of **lab 71** (dependencies).

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean roles-creer-premier-role
```

This target uninstalls/removes what the solution set up on the managed
nodes (packages, files, services, firewall rules) so that you can
re-run the solution from scratch.
