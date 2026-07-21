# 🎯 Challenge — Demonstrate precedence with a playbook

You have seen that `ansible-inventory --host` resolves the variables correctly. The challenge is to **prove dynamically** the resolution on the 3 hosts via a playbook that lays down a marker file containing the value of `app_port` resolved for that host.

## ✅ Objective

Write `solution.yml` that:

1. Targets **all the hosts** (`hosts: all`)
2. Lays down a marker file `/tmp/lab55-port-{{ inventory_hostname }}.txt` that contains the value of `app_port` resolved for the current host
3. Uses the `ansible.builtin.copy:` module (with `content:`)

The inventory to use: **the one of the parent lab** (`../inventory/hosts.yml`), not the one of the challenge.

## 🧩 Instructions

Skeleton to complete:

```yaml
---
- name: Challenge — démontrer la précédence des variables
  hosts: ???                            # all the hosts of the inventory
  become: ???
  gather_facts: false
  tasks:
    - name: Poser un marqueur par hôte avec la valeur de app_port résolue
      ansible.builtin.copy:
        dest: ???                       # /tmp/lab55-port-<inventory_hostname>.txt
        content: "port resolu pour {{ ??? }} : {{ ??? }}\n"
        mode: "0644"
```

> 💡 **Traps**:
>
> - **Variable precedence** (from weakest to strongest):
>   `group_vars/all` < `group_vars/<group>` < `host_vars/<host>`. So on
>   web1, the `host_vars/web1.lab.yml` wins over `group_vars/webservers.yml`.
> - **Challenge inventory**: use `-i inventory/hosts.yml` of the lab (not the
>   root inventory of the repo). Otherwise the `group_vars` are not loaded.
> - **`inventory_hostname`**: it is the name **in the inventory** (`web1.lab`),
>   not the system hostname. To be preferred in playbooks.
> - **`become: false`** is enough: `/tmp` is writable by everyone, and the
>   `ansible` user can write its own files.

Run the solution from the **lab folder**:

```bash
cd labs/inventaires/group-vars-host-vars/
ansible-playbook -i inventory/hosts.yml challenge/solution.yml
```

Check the files on each host:

   ```bash
   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab cat /tmp/lab55-port-web1.lab.txt
   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web2.lab cat /tmp/lab55-port-web2.lab.txt
   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab  cat /tmp/lab55-port-db1.lab.txt
   ```

   Expected outputs:

   ```text
   port resolu pour web1.lab : 9090
   port resolu pour web2.lab : 8080
   port resolu pour db1.lab : 80
   ```

## 🧪 Validation

The `tests/test_precedence.py` script automatically checks:

- The file `/tmp/lab55-port-web1.lab.txt` exists on `web1.lab` and contains `9090` (host_vars wins).
- The file `/tmp/lab55-port-web2.lab.txt` exists on `web2.lab` and contains `8080` (group_vars/webservers wins).
- The file `/tmp/lab55-port-db1.lab.txt` exists on `db1.lab` and contains `80` (group_vars/all wins by default).

```bash
pytest -v challenge/tests/
```

## 🚀 Going further

- Add `app_port: 5555` in `--extra-vars` on the command line and observe: the value **overrides** everything (priority 22 out of 22).
- Add a `group_vars/webservers/main.yml` folder instead of a `webservers.yml` file: Ansible accepts both formats. Prefer the **folder** if you split into several files (`main.yml`, `vault.yml`, `network.yml`).
- Create a new host `db2.lab` in `dbservers` without any specific variable: it inherits `app_port: 80`.

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean inventaires-group-vars-host-vars
```

This target uninstalls/removes what the solution set down on the managed nodes
(packages, files, services, firewall rules) so that you can rerun the solution
from scratch.
