# 🎯 Challenge — nginx on db1.lab, port 8888

You have just deployed **nginx** on the `webservers`, on its default port.
The challenge is to rewrite a playbook that does the **same logic** on
**db1.lab**, but exposing the service on **port 8888**.

This is the chance to apply what you have just learned (idempotent modules,
task order, firewalld opening) on another host, and to discover that
changing a single port number surfaces one more lock on RHEL:
**SELinux**.

## ✅ Objective

Write a playbook named `solution.yml` at the root of **this directory**
(`labs/premiers-pas/premier-playbook/challenge/solution.yml`) that:

1. Targets the `db1.lab` host (`dbservers` group)
2. Installs the `nginx` package
3. Starts and enables the `nginx` service at boot
4. **Configures nginx to listen on port `8888`** instead of 80
5. Makes **SELinux** accept this port
6. Opens port **8888** in firewalld (public zone)
7. Places an `index.html` welcome page with the exact text:
   `Hello from db1.lab — Ansible RHCE 2026`

## 🧩 Instructions

Skeleton to complete (`challenge/solution.yml`):

```yaml
---
- name: "Challenge : nginx sur db1, port 8888"
  hosts: ???
  become: ???
  tasks:
    - name: Installer nginx
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Forcer nginx à écouter sur 8888 (au lieu de 80)
      ansible.builtin.lineinfile:
        path: /etc/nginx/nginx.conf
        regexp: ???                  # match 'listen <port>;' whatever the port
        line: ???                    # mind the indentation inside the server block

    - name: Autoriser SELinux à laisser nginx écouter sur 8888
      community.general.seport:
        ports: ???
        proto: tcp
        setype: ???                  # http_port_t
        state: present

    - name: Ouvrir le port 8888 dans firewalld (zone publique, persistant + immédiat)
      ansible.posix.firewalld:
        port: ???
        permanent: ???
        immediate: ???
        state: ???

    - name: Poser la page d'accueil
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"

    - name: Démarrer et activer nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???
        enabled: ???
```

> 💡 **Traps**:
>
> - **SELinux blocks non-standard ports**: without the
>   `community.general.seport` task, nginx fails to start with a
>   `bind() to 0.0.0.0:8888 failed (13: Permission denied)`. This is the most
>   frequent error on first RHEL playbooks, and opening the firewall changes
>   nothing: they are **two distinct locks**.
> - **When it fails, raise the verbosity**: `ansible-playbook -vvv` shows the
>   module arguments and the raw return, which is usually enough to see what
>   the target actually received. `troubleshooting/verbosite` covers this and
>   the callback plugins; you do not have to wait until you reach it.
> - **You do not need to master SELinux here**: the task above is enough to
>   pass. SELinux has its own lab later (`modules-rhel/selinux`), where
>   booleans, file contexts and `semanage` are covered properly. Meeting it
>   this early is deliberate: on RHEL you hit it from your very first real
>   playbook.
> - **Why 8888 and not 8080**: on RHEL, nginx runs in the SELinux
>   `httpd_t` domain, which the policy already allows on `http_cache_port_t`,
>   which includes 8080. On 8080, the `seport` task would therefore be
>   useless, and you would have learned nothing. On 8888, it is essential.
>   Check for yourself:
>   `semanage port -l | grep -E '^http_(port|cache_port)_t'`.
> - **Task order**: place the welcome page **before** starting
>   nginx, otherwise the first `curl` may land on the default page.
> - **`firewalld`**: `permanent: true` + `immediate: true` together
>   guarantee a persistent + active rule without `--reload`.
> - The welcome page file is `/usr/share/nginx/html/index.html`, nginx's
>   default docroot on RHEL. It is **not** `/var/www/html`,
>   which is Apache's.

Run your solution from the **repo root**:

```bash
ansible-playbook labs/premiers-pas/premier-playbook/challenge/solution.yml
```

Then test:

```bash
curl http://db1.lab:8888
# Must return: Hello from db1.lab — Ansible RHCE 2026
```

## 🧪 Validation

The `tests/test_functional.py` script automatically validates your solution.
It checks on **db1.lab**:

- The `nginx` package is **installed**
- The `nginx` service is **running** and **enabled**
- Port **8888** is **listening**
- Port **8888** carries the SELinux label `http_port_t` (proof of `seport`)
- Port **8888** is open in firewalld (public zone)
- The HTTP request `http://db1.lab:8888` returns **200**
- The page **content** is exactly
  `Hello from db1.lab — Ansible RHCE 2026`
- The solution is **idempotent**: a second run reports no change (RHCE criterion)

To run the tests, from the repo root:

```bash
pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
```

## 🚀 Going further

- Add a **final check** in your playbook with
  `ansible.builtin.uri` that calls `http://localhost:8888` on the managed node
  side and verifies that the returned HTTP code is `200` and that the `content`
  matches.
- Remove the `seport` task, run
  `sudo semanage port -d -t http_port_t -p tcp 8888` on db1, then rerun the
  playbook and read nginx's error message. It is the one you will
  meet in production: learn to recognize it.
- Redo the challenge using a **Jinja2 template** instead of a hardcoded content
  copy (a preview of the `ecrire-code/` section).

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge from a neutral state:

```bash
dsoxlab clean premiers-pas-premier-playbook
```

This target uninstalls/removes what the solution placed on the managed
nodes (packages, files, services, firewall rules) so you can
rerun the solution from scratch.
