# 🎯 Challenge — Write a static inventory from scratch

No inventory is provided to you. You start from a blank page and you write
`inventory/hosts.yml` by hand, just like in task 1 of the exam.

## ✅ Objective

Create the file `inventory/hosts.yml` (at the root of the lab) declaring:

1. A **`webservers`** group containing **web1.lab** and **web2.lab**.
2. A **`dbservers`** group containing **db1.lab**.
3. A parent group **`datacenter`** that aggregates `webservers` and `dbservers`
   via **`children`** (no host of its own).
4. A group variable **`web_role: frontend`** carried by `webservers`.
5. A group variable **`db_role: database`** carried by `dbservers`.
6. A variable **`site: paris`** carried by the **parent** `datacenter`, hence
   inherited by the three hosts.

**No IP address** in the file: the connection goes through the dsoxlab
`ssh_config`, the connection user is `ansible` (the service account dsoxlab
provisions on the VMs).

## 🧩 Instructions

The **connection block** (specific to dsoxlab) is given to you: copy it as is
under `all.vars`, then complete `children` with your groups.

```yaml
---
all:
  vars:
    ansible_user: ansible
    ansible_ssh_common_args: >-
      -F {{ lookup('env', 'HOME') }}/.cache/dsoxlab/ansible-training/ssh_config
      -o StrictHostKeyChecking=no
      -o UserKnownHostsFile=/dev/null
    ansible_ssh_private_key_file: "{{ inventory_dir }}/../../../../ssh/id_ed25519"
    ansible_python_interpreter: /usr/bin/python3
  children:
    webservers:
      hosts:
        ???
        ???
      vars:
        ???
    dbservers:
      hosts:
        ???
      vars:
        ???
    datacenter:
      children:
        ???
        ???
      vars:
        ???
```

> 💡 **Traps**:
>
> - **A host, not a list**: `web1.lab:` (colon), not `- web1.lab`.
> - **A parent group has no `hosts:`**: it only has `children:`. If you put the
>   hosts directly back into `datacenter`, it is no longer a parent, it is a
>   third flat group.
> - **The parent's variable must flow down**: `site` is declared only once, on
>   `datacenter`, and web1/web2/db1 inherit it. Copying it onto each host
>   "works" in the display but misses the objective.
> - **The connection block is mandatory**: without it, `ansible -m ping`
>   reaches no VM and the tests fail on the connection, not on your groups.

## 🔎 Check for yourself before running the tests

```bash
cd labs/inventaires/statiques/

ansible-inventory -i inventory/hosts.yml --graph
# Expected: @datacenter contains @webservers (web1, web2) and @dbservers (db1).

ansible webservers -i inventory/hosts.yml -m ansible.builtin.ping   # 2 pong
ansible datacenter -i inventory/hosts.yml -m ansible.builtin.ping   # 3 pong

ansible-inventory -i inventory/hosts.yml --host db1.lab
# Expected: db_role=database AND site=paris, but NO web_role.
```

## 🧪 Validation

```bash
pytest -v challenge/tests/
```

The tests query the inventory **resolved by Ansible** (`ansible-inventory
--list` / `--host`) and reach the hosts through **ping**: they prove the state,
not the text of the file.

## 🚀 Going further

- Rewrite the same inventory in **INI format** (`inventory/hosts.ini`) and
  check that `ansible-inventory --graph` produces the same graph.
- Move `web_role` out of the inline form into a `group_vars/webservers.yml`
  file next to the inventory: Ansible resolves it the same way.
- Add a second parent `production` that aggregates `datacenter`, and observe
  the cascading inheritance of `site` with `ansible-inventory --host web1.lab`.

## 🧹 Reset

The deliverable of this lab is a local file (`inventory/`, gitignored): there
is nothing to clean up on the VMs. To start over, simply delete your inventory:

```bash
rm -rf labs/inventaires/statiques/inventory/
```
