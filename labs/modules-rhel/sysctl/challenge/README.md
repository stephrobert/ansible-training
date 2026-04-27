# 🎯 Challenge — 4 paramètres sysctl pour durcissement

## ✅ Objectif

Sur **db1.lab**, configurer **4 paramètres `sysctl`** dans un fichier dédié
**`/etc/sysctl.d/99-rhce-lab.conf`**, et les appliquer immédiatement.

| Paramètre | Valeur | Effet |
| --- | --- | --- |
| `net.ipv4.ip_forward` | `1` | Active le routage IPv4 (utile sur un firewall/NAT) |
| `net.ipv4.tcp_syncookies` | `1` | Protection contre les SYN floods |
| `kernel.kptr_restrict` | `2` | Cache les pointeurs kernel dans `/proc` (durcissement) |
| `vm.swappiness` | `10` | Préfère la RAM au swap (perfs) |

## 🧩 Indices

- `ansible.posix.sysctl` est le module à utiliser.
- **`sysctl_file:`** : fichier où écrire la valeur. Si vous l'omettez, le
  paramètre est écrit dans `/etc/sysctl.conf` (file global). Préférez un
  fichier dédié `/etc/sysctl.d/99-<rôle>.conf` (Ansible-friendly,
  versionnable).
- **`reload: true`** : applique immédiatement (`sysctl -p ...`). Sans ça, la
  valeur n'est active **qu'après reboot**.

## 🧩 Squelette

```yaml
---
- name: Challenge - sysctl 4 paramètres
  hosts: db1.lab
  become: true

  tasks:
    - name: Configurer 4 paramètres dans /etc/sysctl.d/99-rhce-lab.conf
      ansible.posix.sysctl:
        name: ???
        value: ???
        state: present
        sysctl_file: ???
        reload: ???
      loop:
        - { name: net.ipv4.ip_forward, value: '1' }
        - { name: net.ipv4.tcp_syncookies, value: '1' }
        - { name: kernel.kptr_restrict, value: '2' }
        - { name: vm.swappiness, value: '10' }
      loop_control:
        label: ???
```

> 💡 **Quote les `value:`** : `'1'`, `'2'`, etc. — `sysctl` aime les chaînes.

**Pièges** :

> - **`sysctl_file:`** : par défaut `/etc/sysctl.conf` (déprécié sur
>   RHEL 9+). Préférer `/etc/sysctl.d/<NN>-<topic>.conf` (numéro de
>   priorité 99 = lu en dernier).
> - **`reload: true`** (défaut) : applique le nouveau réglage **maintenant**
>   (pas seulement à la persistance). Si `false`, il faut un reboot ou
>   `sysctl -p`.
> - **`name:`** = clé sysctl (`net.ipv4.ip_forward`). Format
>   point-séparé, **pas** slash-séparé (`/proc/sys/...`).
> - **Idempotence** : `sysctl:` compare la valeur actuelle. Si elle
>   match, `changed=0`. Vrai pour persistance ET runtime simultanément.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-rhel/sysctl/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/sysctl.d/99-rhce-lab.conf"
ansible db1.lab -m ansible.builtin.command -a "sysctl -n net.ipv4.ip_forward vm.swappiness"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-rhel/sysctl/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-rhel/sysctl clean
```

## 💡 Pour aller plus loin

- **`state: absent`** : supprime le paramètre du fichier (mais ne réinitialise
  **pas** la valeur runtime — il faudra un reboot ou un sysctl explicite).
- **Auditer les sysctl actifs** : `sysctl -a | grep ip_forward` ou
  `cat /proc/sys/...`.
- **Pattern durcissement CIS** : un rôle Ansible « cis-rhel-baseline » pose
  ~30 paramètres sysctl. C'est exactement le pattern à industrialiser.
- **Lint** :

   ```bash
   ansible-lint labs/modules-rhel/sysctl/challenge/solution.yml
   ```
