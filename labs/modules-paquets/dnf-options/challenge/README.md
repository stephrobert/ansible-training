# 🎯 Challenge — `dnf:` avec options EPEL

## ✅ Objectif

Sur **db1.lab**, activer le dépôt **EPEL** (Extra Packages for Enterprise
Linux) et installer 2 paquets qui n'existent que dans EPEL.

C'est l'occasion d'utiliser **les options avancées** du module
`ansible.builtin.dnf` qui n'existent pas dans `ansible.builtin.package` :
`enablerepo`, `update_cache`, `exclude`.

## 🧩 Étapes

1. **Installer `epel-release`** (paquet officiel qui ajoute le repo EPEL à
   `/etc/yum.repos.d/`).
2. **Installer `htop` et `ncdu`** (deux outils EPEL) avec :
   - `enablerepo: epel` — active explicitement le repo (par sécurité, même
     s'il est déjà activé après `epel-release`).
   - `update_cache: true` — refresh du cache dnf avant l'install.
   - `exclude: kernel*` — protège contre une mise à jour kernel par effet de
     bord (un metapackage qui tirerait du kernel).

## 🧩 Squelette

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

> 💡 **Pièges** :
>
> - **`enablerepo:`** active un repo **temporairement** pour cette
>   transaction (équivalent `dnf --enablerepo=`). Pour persister, modifier
>   `/etc/yum.repos.d/<repo>.repo`.
> - **`update_cache: true`** rafraîchit la metadata. Coûteux (réseau) —
>   éviter sur chaque tâche, faire une seule fois en `pre_tasks`.
> - **`exclude:`** : liste de paquets à NE PAS toucher. Utile pour pinner
>   un paquet à une version spécifique.
> - **`security: true`** : installe seulement les advisories sécurité.
>   Combiné avec `state: latest`, applique les patches sans bumper
>   d'autres versions.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-paquets/dnf-options/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "rpm -q epel-release htop ncdu"
ansible db1.lab -m ansible.builtin.command -a "ls /etc/yum.repos.d/ | grep -i epel"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-paquets/dnf-options/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-paquets/dnf-options clean
```

## 💡 Pour aller plus loin

- **`disablerepo: '*'` + `enablerepo: epel`** : ne tire **que** du repo EPEL.
  Utile pour des audits où on veut isoler une source de paquets.
- **`disable_gpg_check: false`** (défaut) : exige une signature GPG valide.
  En production, **gardez ce défaut**.
- **`security: true`** : n'installe que les **mises à jour de sécurité**
  (combiné à `state: latest`).
- **`autoremove: true`** : enlève les dépendances orphelines après
  désinstallation.
- **Lint** :

   ```bash
   ansible-lint labs/modules-paquets/dnf-options/challenge/solution.yml
   ```
