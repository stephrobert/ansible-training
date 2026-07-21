# 🎯 Challenge — Handlers and meta of the webserver role

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** uses the `webserver`
role with a **custom port** to demonstrate that:

1. The **3 handlers** (`Restart nginx`, `Reload nginx`, `Notify deployment`)
   are indeed triggered at deployment.
2. The role's `meta/main.yml` is read correctly (verifiable via
   `ansible-galaxy role list`).

## 🧩 Hints

The role accepts variables (override of the `defaults/`):

| Variable | Default | Override? |
| --- | --- | --- |
| `webserver_listen_port` | `80` | ✅ → **`8080`** (the test expects this port) |
| `webserver_index_content` | `<h1>Hello…</h1>` | ✅ → custom message including `inventory_hostname` |

The challenge checks via the tests:

- `nginx` is `running` and listens on **port 8080**
- `/var/log/webserver-deploy.log` exists and contains `db1.lab`
- `/var/log/deploy-notification.log` exists and contains `Deployment completed`,
  `db1.lab`, and **`8080`** (proof that the handler indeed read the
  overridden variable)

## 🧩 Skeleton

```yaml
---
- name: Challenge - handlers déclenchés sur db1
  hosts: ???
  become: ???

  roles:
    - role: webserver
      vars:
        webserver_listen_port: ???           # 8080
        webserver_index_content: "{{ ??? }}"  # custom message with inventory_hostname
```

> 💡 **Pitfalls**:
>
> - **Role-level override**: `vars:` under `- role: webserver` targets
>   only this role, and it is a **role param** (priority 20), not a
>   play `vars:` (12). Two indentation lines apart, and the variable
>   changes category: the role param even beats the role's `vars/main.yml`
>   (15), where a play `vars:` loses against them.
> - **3 handlers expected**: `Restart nginx`, `Reload nginx`, `Notify
>   deployment`. The `meta/main.yml` cannot define a handler: that
>   stays in `roles/<role>/handlers/main.yml`.
> - **Reading variables on the handler side**: `webserver_listen_port` must
>   be readable in the handler (which runs at the end of the play). If you
>   use `{{ webserver_listen_port }}` in the handler, it **reads the
>   current value** (post-override): that is what we want.
> - **Idempotence**: the `Notify deployment` handler is notified by the
>   "Tracer le déploiement" task, which writes **stable** content (the host and the
>   applied port). So it only reports `changed` if the deployed state changes
>   for real. On the identical 2nd run, `changed=0` and no handler runs:
>   that is what `test_solution_idempotente` checks.

## 🚀 Run

```bash
ansible-playbook labs/roles/handlers-meta/challenge/solution.yml
```

🔍 **Expected output**: 3 `RUNNING HANDLER` banners (for Restart, Reload,
Notify deployment) on the 1st run.

```bash
# Checks
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo ss -tlnp | grep 8080'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /var/log/deploy-notification.log'
```

## 🧪 Automated validation

```bash
pytest -v labs/roles/handlers-meta/challenge/tests/
```

The test checks on db1:

- `nginx` running.
- `/var/log/webserver-deploy.log` contains `db1.lab`.
- `/var/log/deploy-notification.log` contains `Deployment completed` + `db1.lab` + `8080`.
- `nginx` listens on `:8080`.

## 🧹 Reset

```bash
dsoxlab clean roles-handlers-meta
```

## 💡 Going further

- **`ansible-galaxy role list`**: validates that the `meta/main.yml` is readable.
  If you get a parsing error, it is a YAML problem.
- **Role inspection**:

  ```bash
  ansible-doc -t role labs/roles/handlers-meta/roles/webserver
  # Displays the documented variables + supported platforms
  ```

- **Lint**:

  ```bash
  ansible-lint --profile production labs/roles/handlers-meta/
  ```

  The `production` profile checks in particular that `meta/main.yml` indeed
  contains `galaxy_info`, `platforms`, and `min_ansible_version`.
