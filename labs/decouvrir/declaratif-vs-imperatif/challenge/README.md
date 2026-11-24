# The script that adds a line every night

## The situation

A colleague deploys the landing page of **web1.lab** with a Bash script fired
by cron. It works. Except visitors now read *"Servi par web1.lab"* three times
on the home page, then four, then five. Nobody touched the page: the script
appends the line at every run and never asks whether it is already there. The
incident is small, the lesson is not.

From **control-node.lab**, you are going to watch why the same job, written
declaratively, cannot drift.

Your mission:

1. Run the **Bash script three times** against `web1.lab` and watch the line
   counter climb: that is drift, live.
2. Reset the node, then run the **playbook three times** and observe the page
   stay at exactly one line.
3. Read the second `PLAY RECAP`: **`changed=0`** is the mechanical proof of
   idempotence, not a matter of opinion.
4. Compare the two files and name what the `lineinfile:` module compares before it
   writes anything at all.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/ (in French)

## 🎯 Challenge — Convert the imperative Bash script into an idempotent playbook

### ✅ Objective

The file `scripts/install-nginx-impératif.sh` deploys nginx **imperatively**: it
chains commands and, worse, **appends** a line to the home page on every run, so
it **drifts**. Your job is the EX294 classic: **rewrite it as a declarative
Ansible playbook** that produces the **same system state** on `web1.lab`, but
**converges** instead of drifting.

Write your playbook in `challenge/solution.yml`. It must reach exactly this
state, and reach it **idempotently** (`changed=0` on the second run).

| Item | Expected value |
| --- | --- |
| Target host | `web1.lab` |
| Package | `nginx` installed (`state: present`) |
| Service | `nginx` started **and** enabled at boot |
| Firewall | service `http` open, **permanent and immediate** |
| Home page | `/usr/share/nginx/html/index.html` contains **exactly one** `<p>Servi par ...</p>` line |
| Idempotence | 2nd run of the playbook → `changed=0` in `PLAY RECAP` |

### 🧩 Skeleton — `challenge/solution.yml`

```yaml
---
- name: Deploy nginx declaratively (idempotent equivalent of the Bash script)
  hosts: ???                      # the node that actually serves the page
  become: ???

  tasks:
    - name: Install the nginx package
      ansible.builtin.dnf:
        name: ???
        state: ???                # present, not latest (see traps)

    - name: Open the http service in firewalld
      ansible.posix.firewalld:
        service: ???
        permanent: ???            # survive a reload / reboot
        immediate: ???            # take effect now, without a reload
        state: enabled

    - name: Start nginx and enable it at boot
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Ensure a SINGLE "Servi par ..." line in index.html
      ansible.builtin.lineinfile:
        path: /usr/share/nginx/html/index.html
        regexp: ???               # the pattern that identifies the line
        line: ???                 # e.g. "<p>Servi par {{ inventory_hostname_short }}</p>"
        state: present
        create: false
```

### 💡 Traps

- **State, not commands.** The Bash script `echo "..." | tee -a` appends **one
  line per run**: that is the drift. Do **not** translate it into a
  `command:`/`shell:` task. Describe the desired **state** with a module that
  already knows how to converge (`lineinfile` with a `regexp`, or `copy` /
  `template`). This is the whole point of the exercise.
- **`lineinfile` regexp.** The `regexp` must match **the line you write**. If it
  does not, `lineinfile` never recognises its own output and appends a new line
  on every run: you have reinvented the Bash drift in YAML. `changed=0` on the
  second pass is what proves you got it right.
- **`present`, not `latest`.** `state: latest` re-queries the repository and can
  report `changed` on an upstream update: that is a drift too. Use
  `state: present`.
- **Permanent firewall.** A runtime-only rule disappears on the next
  `firewall-cmd --reload`. Set `permanent: true` **and** `immediate: true`.
- **FQCN.** Use fully qualified names (`ansible.builtin.dnf`,
  `ansible.posix.firewalld`, `ansible.builtin.systemd_service`,
  `ansible.builtin.lineinfile`). `ansible-lint --profile production` requires it.

### 🚀 Launch

```bash
# From the repo root, once challenge/solution.yml is written:
ansible-playbook labs/decouvrir/declaratif-vs-imperatif/challenge/solution.yml

# Run it a second time: PLAY RECAP must show changed=0 everywhere.
ansible-playbook labs/decouvrir/declaratif-vs-imperatif/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/decouvrir/declaratif-vs-imperatif/challenge/tests/
```

The pytest suite proves the **system state**, not that a command ran:

- `nginx` is installed, started and enabled at boot.
- `http` is open in firewalld, at runtime **and** permanent.
- `index.html` contains **exactly one** `<p>Servi par ...</p>` line.
- nginx actually serves that page over HTTP.
- The playbook is **idempotent**: a second run yields `changed=0`.

### 🧹 Reset

```bash
dsoxlab clean decouvrir-declaratif-vs-imperatif
```

Removes the `Servi par ...` line so you can replay from a clean state.

### 💡 Going further

- Make the **Bash** script idempotent by hand
  (`grep -q "Servi par" ... || echo ...`). It works, but you reinvented
  idempotence for a single line. Now imagine it across 50 files: that is why the
  declarative model wins.
- Swap `lineinfile` for `copy` + `content:` or a `template`. `copy` is
  idempotent by **checksum** (the whole file), `lineinfile` by **regexp** (one
  line). When is each the right tool?
