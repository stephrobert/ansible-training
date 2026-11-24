# Pull EPEL tooling onto db1 without dragging the kernel along

## The situation

The DBA wants two diagnostic tools on **db1.lab** to chase down a disk
saturation: a live process viewer and a directory usage explorer. Neither ships
in the base AlmaLinux repositories, they live in EPEL. The last colleague who
enabled a third-party repo also let a metapackage pull a fresh kernel through,
and the database rebooted onto an untested kernel. That will not happen twice.
You work from **control-node.lab**, and the transaction stays under control.

Your mission:

1. Add the **EPEL** repository to **db1.lab** through its official release
   package, rather than hand-writing a `.repo` file.
2. Install the two diagnostic tools by **enabling EPEL explicitly** for that
   transaction and **refreshing the metadata cache** beforehand.
3. **Exclude every kernel package** from the transaction: no dependency may
   bump the kernel of a production database by side effect.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf-options/ (in French)

## 🎯 Challenge — `dnf:` with EPEL options

### ✅ Objective

On **db1.lab**, enable the **EPEL** repository (Extra Packages for Enterprise
Linux) and install 2 packages that only exist in EPEL.

This is the chance to use **the advanced options** of the
`ansible.builtin.dnf` module that do not exist in `ansible.builtin.package`:
`enablerepo`, `update_cache`, `exclude`.

### 🧩 Steps

1. **Install `epel-release`** (official package that adds the EPEL repo to
   `/etc/yum.repos.d/`).
2. **Install `htop` and `ncdu`** (two EPEL tools) with:
   - `enablerepo: epel`: enables the repo explicitly (for safety, even
     if it is already enabled after `epel-release`).
   - `update_cache: true`: refresh the dnf cache before the install.
   - `exclude: kernel*`: protects against a kernel update as a side
     effect (a metapackage that would pull in the kernel).

### 🧩 Skeleton

```yaml
---
- name: Challenge - dnf options EPEL
  hosts: db1.lab
  become: true

  tasks:
    - name: Installer le paquet epel-release
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Installer htop et ncdu depuis EPEL
      ansible.builtin.dnf:
        name: ???
        state: present
        enablerepo: ???
        update_cache: ???
        exclude: ???
```

> 💡 **Traps**:
>
> - **`enablerepo:`** enables a repo **temporarily** for this
>   transaction (equivalent to `dnf --enablerepo=`). To persist, modify
>   `/etc/yum.repos.d/<repo>.repo`.
> - **`update_cache: true`** refreshes the metadata. Costly (network):
>   avoid it on every task, do it only once in `pre_tasks`.
> - **`exclude:`**: list of packages NOT to touch. Useful to pin
>   a package to a specific version.
> - **`security: true`**: installs only the security advisories.
>   Combined with `state: latest`, applies the patches without bumping
>   other versions.

### 🚀 Launch

```bash
ansible-playbook labs/modules-paquets/dnf-options/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "rpm -q epel-release htop ncdu"
ansible db1.lab -m ansible.builtin.command -a "ls /etc/yum.repos.d/ | grep -i epel"
```

### 🧪 Automated validation

```bash
pytest -v labs/modules-paquets/dnf-options/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-paquets-dnf-options
```

### 💡 Going further

- **`disablerepo: '*'` + `enablerepo: epel`**: pulls **only** from the EPEL repo.
  Useful for audits where you want to isolate a package source.
- **`disable_gpg_check: false`** (default): requires a valid GPG signature.
  In production, **keep this default**.
- **`security: true`**: installs only the **security updates**
  (combined with `state: latest`).
- **`autoremove: true`**: removes orphaned dependencies after
  uninstallation.
- **Lint**:

   ```bash
   ansible-lint labs/modules-paquets/dnf-options/challenge/solution.yml
   ```
