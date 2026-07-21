# 🎯 Challenge — Discover, use, and validate with `ansible-navigator`

## ✅ Objective

Write `challenge/solution.yml` (play targeting `db1.lab`) that uses **Automation
content navigator** for the whole loop and leaves the following state.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Exploration proof | `/tmp/lab-navigator-doc.txt`, `0644`, owner `root`, contains `ansible.posix.sysctl` |
| Kernel state | `vm.swappiness = 42`, live **and** written under `/etc/sysctl.d/70-navigator-lab.conf` |
| Inventory proof | `/tmp/lab-navigator-inventory.txt`, `0644`, owner `root`, contains `db1.lab` and the group `webservers` |
| Idempotency | A second run reports `changed=0` |

`ansible-navigator` runs on the **control node**: call it with `delegate_to:
localhost` and `become: false`. Pass `--mode stdout --execution-environment false`
so it stays scriptable and does not pull an EE image.

## 🧩 Hints

### (a) Discover the module and drop the proof

```yaml
- name: Discover the sysctl module with ansible-navigator doc
  ansible.builtin.command: >-
    ansible-navigator doc ??? --mode stdout --execution-environment false
  register: nav_doc
  changed_when: false
  delegate_to: localhost
  become: false

- name: Deposit the exploration proof on db1.lab
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-doc.txt
    content: "{{ nav_doc.stdout }}\n"
    owner: root
    group: root
    mode: "0644"
```

> 💡 The FQCN you pass to `doc` is the one that must appear in the proof file.
> Find it with `ansible-navigator collections` or `ansible-navigator doc -l` if you
> are unsure which collection ships the `sysctl` module.

### (b) Use the discovered module (verifiable state)

```yaml
- name: Apply the discovered module
  ansible.posix.sysctl:
    name: vm.swappiness
    value: "42"
    sysctl_set: ???        # ← also change the LIVE value
    state: present
    reload: true
    sysctl_file: /etc/sysctl.d/70-navigator-lab.conf
```

### (c) Validate an inventory with the navigator

```yaml
- name: Write an inventory to validate (control node)
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-inventory-src.yml
    mode: "0644"
    content: |
      all:
        children:
          webservers:
            hosts:
              db1.lab:
                ansible_host: 127.0.0.1
  delegate_to: localhost
  become: false

- name: Validate the inventory with ansible-navigator inventory --list
  ansible.builtin.command: >-
    ansible-navigator inventory -i /tmp/lab-navigator-inventory-src.yml --list \
      --mode stdout --execution-environment false
  register: nav_inventory
  changed_when: false
  delegate_to: localhost
  become: false

- name: Deposit the inventory proof on db1.lab
  ansible.builtin.copy:
    dest: /tmp/lab-navigator-inventory.txt
    content: "{{ nav_inventory.stdout }}\n"
    owner: root
    group: root
    mode: "0644"
```

> 💡 **Pitfalls**:
>
> - Without `--mode stdout`, `ansible-navigator` opens its **TUI** and blocks any
>   script or test.
> - Without `--execution-environment false`, it tries to **pull an EE image** and
>   run inside a container: heavy and network-bound for this exercise.
> - A `command:` that invokes navigator is **read-only**: set `changed_when: false`
>   or your playbook will never be idempotent.

## 🚀 Launch

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

The pytest+testinfra test validates:

- the exploration proof exists (`0644`, root) and cites `ansible.posix.sysctl`;
- `vm.swappiness` is `42` live on `db1.lab` and persisted under `/etc/sysctl.d/`;
- the inventory proof resolves `db1.lab` and the `webservers` group;
- the solution is **idempotent** (RHCE criterion).

## 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
