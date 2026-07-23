# Lab 01 — Declarative vs imperative (why Ansible is not Bash)

> ⚠️ **First lab: check that your 4 VMs are running before you start.**
>
> All labs run on **4 AlmaLinux VMs** provisioned locally via libvirt/KVM
> (`control-node`, `web1`, `web2`, `db1`). If you are landing on this repo
> for the first time, you must create them **only once**:
>
> ```bash
> cd <ansible-training>          # repo root
> mise install                 # installs Ansible + libvirt + tools (~3 min, 1×)
> dsoxlab provision                 # creates the 4 VMs + prepares the managed nodes (~5 min)
> mise run setup-hosts                 # adds web1.lab/web2.lab/db1.lab to /etc/hosts (sudo)
> mise run setup-ssh            # 'ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab' uses the repo key
> `dsoxlab status`                          # → 4 "pong" expected (final validation)
> ```
>
> Quick check at any time:
>
> ```bash
> ansible all -m ansible.builtin.ping
> # control-node.lab | SUCCESS => {"ping": "pong"}
> # web1.lab         | SUCCESS => {"ping": "pong"}
> # web2.lab         | SUCCESS => {"ping": "pong"}
> # db1.lab          | SUCCESS => {"ping": "pong"}
> ```
>
> | Action | Command |
> | --- | --- |
> | Check the VMs state | `virsh list --all` |
> | Check the lab hostnames state | `mise run setup-hosts` |
> | Snapshot before a risky lab | `mise run snapshot` |
> | Restore the snapshot | `mise run restore` |
> | Destroy all VMs (after the training) | `dsoxlab destroy` |
> | Remove the hostnames from `/etc/hosts` | `mise run remove-hosts` |
> | State of the lab SSH config | `mise run setup-ssh` |
> | Remove the lab SSH config | `mise run remove-ssh` |
>
> For the details (network topology, required resources, troubleshooting),
> see the [root README](../../../README.md), sections "Lab topology" and
> "Workstation prerequisites".

## 🧠 Recap and recommended reading

> 📖 **Before practicing, read the companion blog guide.** It lays out the
> theoretical context (Ansible history, Push vs Pull, idempotence) that this
> lab illustrates concretely:
>
> 🔗 [**Declarative vs imperative: the same task, two philosophies**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/)
>
> ⏱ Reading time: ~10 min. The guide explains the **why**, this lab makes you
> feel the **how** in practice. The two together = guaranteed mental click.

### In 30 seconds

**Imperative** = you describe **the steps** ("install nginx, add this line, start the service"). On every rerun, the script redoes all the steps, and it **drifts** if one of them is not idempotent (e.g. appending a line).

**Declarative** = you describe **the desired state** ("nginx present, home page containing this line, service started"). Ansible compares with the current state and **acts only when needed**. On the second pass, nothing left to do: that is the `changed=0` signal in the `PLAY RECAP`.

This is the **mental click** of the training: without understanding this difference, you write Bash in YAML and miss what Ansible brings.

## 🎯 Objectives

By the end of this lab, you will have **seen with your own eyes**:

1. A naive Bash script that **drifts** on every run against the same target.
2. An Ansible playbook that achieves the same goal and **converges** toward the desired state.
3. The concrete difference between **idempotent** and **non-idempotent**.
4. The `changed=0` signal on the second pass: the mechanical proof of idempotence.

## 🔧 Preparation

Check that the lab VMs are running and that `web1.lab` responds:

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
```

Expected response: `web1.lab | SUCCESS => {"ping": "pong"}`. If you get `UNREACHABLE`, run `dsoxlab provision` at the repo root.

> 💡 **Note**: this lab ships turnkey (`playbook.yml` + Bash script). You have **nothing to write**: you are going to **observe** the difference. The following labs will ask you, in turn, to write the code.

## ⚙️ Lab tree

```text
labs/decouvrir/declaratif-vs-imperatif/
├── README.md                           ← this file
├── playbook.yml                        ← the declarative Ansible equivalent
├── scripts/
│   └── install-nginx-impératif.sh      ← the naive Bash script
└── challenge/
    └── tests/
        └── test_*.py                   ← pytest+testinfra that validates convergence
```

## 📚 Exercise 1 — Read the imperative Bash script

Open the script and read it **before running it**:

```bash
cat labs/decouvrir/declaratif-vs-imperatif/scripts/install-nginx-impératif.sh
```

Spot the 3 steps: (1) install nginx, (2) **add a line** `Servi par <hostname>` to `index.html`, (3) start nginx.

🔍 **Observation to anticipate**: step (2) uses `echo "..." >> index.html`, an **append**. Nothing checks whether the line is already there. On every rerun, one more line is added.

## 📚 Exercise 2 — Watch the Bash script drift

Run the script **3 times** in a row, and watch what piles up:

```bash
cd labs/decouvrir/declaratif-vs-imperatif
for i in 1 2 3; do
  ansible web1.lab -b -m ansible.builtin.script \
    -a "scripts/install-nginx-impératif.sh"
done
```

🔍 **Observation** (expected output):

```text
--- Run #1 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 1
--- Run #2 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 2
--- Run #3 ---
OK : nginx déployé. Occurrences de 'Servi par' dans la page : 3
```

On every run, **the counter climbs by one line**: that is the drift. Check on the managed node:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'sudo grep -n "Servi par" /usr/share/nginx/html/index.html'
```

You see **3 accumulated** `<p>Servi par web1.lab</p>` lines. This is the **drift** typical of the imperative model: the script does not check the state, it `tee -a` blindly on every call.

> 💡 **Technical detail**: `/usr/share/nginx/html/index.html` is actually a **symbolic link** to `/usr/share/testpage/index.html`, a file shipped by the `almalinux-logos-httpd` package (nginx pulls it via `system-logos-httpd`: that `httpd` name is a historical legacy of the shared test page, not an Apache dependency). So `tee -a` modifies the **real file** pointed to by the link, and that is what persists between runs if nothing purges it. The lab's `cleanup.yaml` does precisely this cleanup via `sed -i '/<p>Servi par /d' ...`.

## 📚 Exercise 3 — Watch the Ansible playbook converge

Reset the state (`dsoxlab clean` uninstalls nginx and purges the file) then
run the playbook **3 times**:

```bash
dsoxlab clean decouvrir-declaratif-vs-imperatif
for i in 1 2 3; do ansible-playbook playbook.yml; done
```

🔍 **Observation**: on every run, `index.html` **always contains 1 line**. Check:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'sudo cat /usr/share/nginx/html/index.html'
```

The playbook compared the current state to the desired state, saw it was already compliant, and **did nothing**. Look also at the `PLAY RECAP` of the second run: `changed=0` everywhere. This is **idempotence** in action.

## 📚 Exercise 4 — Compare the `playbook.yml` and the script

Open the two files side by side:

```bash
cat labs/decouvrir/declaratif-vs-imperatif/playbook.yml
cat labs/decouvrir/declaratif-vs-imperatif/scripts/install-nginx-impératif.sh
```

🔍 **Observation**:

- The Bash script **chains commands**, with no memorized state.
- The playbook **declares** a state (`state: present`, `state: started`, exact line via `lineinfile:` + `regexp:`). The `lineinfile:` module **compares the line matched by the regexp** before writing: no write if it already says the right thing.
- The playbook is **shorter** because it relies on the native idempotence of the `dnf`, `lineinfile`, `systemd` modules.

## 📚 Exercise 5 — Verify idempotence through the tests

```bash
`dsoxlab check <id-du-lab>`
```

This target:

1. Runs the `pytest+testinfra` suite (checks that nginx is installed/running, that `index.html` contains **exactly** one `Servi par` line).
2. Reruns the playbook one more time and **greps** `changed=0` in the output: proof of strict idempotence.

🔍 **Observation**: if you had accidentally written the playbook with a non-idempotent `shell:` task, the `changed=0` test would fail. This is the automatic guarantee the whole training is built around.

## 📚 Exercise 6 — Clean up

```bash
`dsoxlab clean <id-du-lab>`
```

Uninstalls nginx, removes the firewalld rule, deletes `index.html`. The lab is ready to be replayed from scratch.

## 🔍 Observations to note

- **Imperative** = sequence of steps; the result depends on the **number of times** you run it.
- **Declarative** = desired state; the result depends only on the **described target**.
- A module is said to be **idempotent** if the second run changes nothing. Almost all `ansible.builtin.*` modules are, except `shell:` and `command:` (which re-execute every time).
- The final `PLAY RECAP` shows `changed=0`: this is the **mechanical signal** of an idempotent playbook. It is the criterion we will look for in all the following labs.
- `creates:` / `removes:` let you make a `shell:` idempotent (it runs only if the file marker is absent / present).

## 🤔 Reflection questions

1. Imagine a Bash script that must add `PermitRootLogin no` to `/etc/ssh/sshd_config`. How do you make it idempotent **without** Ansible? What pitfalls (regex, already-commented line, line with different spacing)?

2. The playbook uses `lineinfile:` + `regexp:` to set one line of `index.html`. Why is it idempotent even when the line is already there? What does the module compare?

3. If a team ships 200 servers and each one receives this lab, is the **final result** identical for 1 or 200 runs of the playbook? And with the Bash script?

## 🚀 Going further

- **Make the Bash script idempotent**: add `grep -q "Servi par" /usr/share/nginx/html/index.html || echo "..." >>` to stop drifting. Notice: it is doable, but we reinvented idempotence by hand for **a single** line. Imagine it across 50 files.
- **Replace `lineinfile:` with `copy:` + `content:`** in `playbook.yml`. Compare: `lineinfile:` is idempotent by regexp (one line, the rest of the file is left alone), `copy:` by checksum (the whole file, which it overwrites). When should you prefer one over the other?
- **Add `creates: /var/lib/nginx-installed.flag`** on a dummy `ansible.builtin.shell:` task then observe the `skipped` on the second run: it is the bridge between `shell:` and idempotence.

## 🔍 Linting with `ansible-lint`

This lab ships turnkey: no `lab.yml` or `challenge/solution.yml` to write. You
can still lint the lab's `playbook.yml` to see what a clean `ansible-lint`
output looks like:

```bash
ansible-lint labs/decouvrir/declaratif-vs-imperatif/playbook.yml
ansible-lint --profile production labs/decouvrir/declaratif-vs-imperatif/playbook.yml
```

Expected output: `Passed: 0 failure(s), 0 warning(s)`.

> 💡 **Key takeaway**: `ansible-lint --profile production` is the RHCE 2026
> standard. It checks FQCN, `name:` on every task, quoted modes,
> idempotence, non-deprecated modules. Adopt it from your very first playbooks.
