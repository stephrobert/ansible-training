# 🎯 Challenge — Complete play on db1 with nginx

You wrote a complete play with `pre_tasks` / `tasks` / `post_tasks` / `handlers`. The challenge **reproduces this pattern** on another host (`db1.lab`) to check that you master the **anatomy of a professional play**. The deployed software does not change: it is indeed the structure of the play that is the subject, not the installed package.

> The **parallelism** concepts (`serial:`, `max_fail_percentage:`, `strategy:`) are the subject of [lab 09](../../parallelisme-strategies/), they are **not** required here.

## ✅ Objective

Write `solution.yml` at the root of **this directory**
(`labs/ecrire-code/plays-et-tasks/challenge/solution.yml`) that:

1. Targets **a single host**: `db1.lab` (group `dbservers`)
2. Uses **`pre_tasks` + `tasks` + `post_tasks` + `handlers`** as in the main exercise
3. Lays down a marker file `/tmp/challenge-predeploy-db1.txt` in `pre_tasks`
4. Installs `nginx` + starts it + enables it
5. Opens the `http` service in **firewalld** (public zone, `permanent: true` + `immediate: true`) so the page is reachable
6. Lays down a welcome page that returns `Challenge OK from db1.lab` (rather than the default page)
7. **Notifies** the handler `Restart nginx` when the page is modified
8. The handler restarts nginx via `ansible.builtin.systemd state: restarted`
9. Lays down a marker file `/tmp/challenge-postdeploy-db1.txt` in `post_tasks`

## 🧩 Instructions

Skeleton to complete:

```yaml
---
- name: "Challenge : play complet sur db1 avec nginx"
  hosts: ???
  become: ???
  pre_tasks:
    - name: Marqueur predeploy
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-predeploy-db1.txt
        content: "predeploy {{ inventory_hostname }}\n"   # STABLE content
        mode: "0644"

  tasks:
    - name: Installer nginx
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Démarrer + activer nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???
        enabled: ???

    - name: Ouvrir le service http dans firewalld
      ansible.posix.firewalld:
        service: ???                       # http
        permanent: ???
        immediate: ???
        state: enabled

    - name: Poser la page d'accueil custom
      ansible.builtin.copy:
        dest: ???                          # /usr/share/nginx/html/index.html
        content: "Challenge OK from {{ ??? }}\n"
        mode: "0644"
      notify: Restart nginx

  post_tasks:
    - name: Marqueur postdeploy (son mtime prouvera l'ordre)
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-postdeploy-db1.txt
        content: "postdeploy {{ inventory_hostname }}\n"  # STABLE content
        mode: "0644"

  handlers:
    - name: Restart nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???                         # restarted
```

> 💡 **Traps**:
>
> - **Execution order**: `pre_tasks` → `tasks` → handlers (notified) →
>   `post_tasks`. If you put the predeploy marker in `tasks:`, the
>   test `mtime predeploy < postdeploy` can fail.
> - **The marker content must be STABLE**: `predeploy db1.lab`, not
>   `predeploy db1.lab at 2026-07-17T09:12:33Z`. What proves the order is
>   the **mtime** of the two files, which the kernel lays down at the write, and which the
>   test compares. The content proves nothing: `ansible_date_time` carries
>   the time of the **fact collection**, not that of the write, and
>   `ansible.cfg` caches it for 2 hours: the two markers would therefore carry
>   the SAME time and the timestamp would not even prove the order expected
>   of it.
> - **A timestamp in the `content:` breaks idempotence**: the content
>   differs on every run, `copy:` rewrites, and `test_solution_idempotente`
>   requires `changed=0` on the second pass. Your playbook would fail.
> - **The test looks for** `Challenge OK from db1.lab` exactly (with the
>   FQDN). Use `inventory_hostname`, not `ansible_hostname` (which is
>   the short hostname).
> - **The nginx docroot on RHEL is `/usr/share/nginx/html`**, not
>   `/var/www/html` (Apache's). Writing `index.html` there directly replaces
>   the default page: unlike Apache, there is no
>   `welcome.conf` to neutralize beforehand.

Run the solution from the **repo root**:

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/challenge/solution.yml
```

Then test:

```bash
curl http://db1.lab
```

The `curl` must return exactly: `Challenge OK from db1.lab`

## 🧪 Validation

The `tests/test_functional.py` script automatically checks:

- The file `/tmp/challenge-predeploy-db1.txt` exists on `db1.lab` and contains the hostname
- The `nginx` package is installed
- The `nginx` service is `running` and `enabled`
- Port `80` is `listening`
- Port `80` is open in firewalld (public zone)
- The HTTP request `http://db1.lab` returns **200** and contains `Challenge OK from db1.lab`
- The file `/tmp/challenge-postdeploy-db1.txt` exists and contains the hostname
- The `predeploy` file is **earlier** than the `postdeploy` file (proof of the execution order)
- The **second pass** of the playbook changes nothing (`changed=0`)

To run the tests, from the repo root:

```bash
pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
```

## 🚀 Going further

- Add a `pre_tasks` that calls a `uri:` module toward a non-existent endpoint, check that the `pre_tasks` fails **before** `tasks` run (proof of the order `pre_tasks` → `tasks`).
- Add `meta: flush_handlers` at the end of `tasks:` and observe the exact moment when the handler runs, see [lab 06](../../handlers/).
- For the `serial:`, `strategy:` and `max_fail_percentage:` concepts, move on to [lab 09](../../parallelisme-strategies/).

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean ecrire-code-plays-et-tasks
```

This target uninstalls/removes what the solution laid down on the managed
nodes (packages, files, services, firewall rules) so that you can
rerun the solution from scratch.
