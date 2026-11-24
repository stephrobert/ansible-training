# Installer l'outillage EPEL sur db1 sans embarquer le kernel

## La situation

Le DBA veut deux outils de diagnostic sur **db1.lab** pour traquer une
saturation disque : un visualiseur de processus en direct et un explorateur
d'occupation de répertoires. Aucun des deux n'existe dans les dépôts de base
d'AlmaLinux : ils vivent dans EPEL. Le dernier collègue qui a activé un dépôt
tiers a aussi laissé un metapaquet tirer un kernel neuf, et la base de données a
redémarré sur un noyau non testé. Cela ne se reproduira pas. Vous travaillez
depuis **control-node.lab**, et la transaction reste sous contrôle.

Votre mission :

1. Ajouter le dépôt **EPEL** sur **db1.lab** via son paquet officiel de
   release, plutôt qu'en écrivant un fichier `.repo` à la main.
2. Installer les deux outils de diagnostic en **activant EPEL explicitement**
   pour cette transaction et en **rafraîchissant le cache de metadata** au
   préalable.
3. **Exclure tous les paquets kernel** de la transaction : aucune dépendance ne
   doit faire monter le noyau d'une base de production par effet de bord.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf-options/

## 🎯 Challenge — `dnf:` avec options EPEL

### ✅ Objectif

Sur **db1.lab**, activer le dépôt **EPEL** (Extra Packages for Enterprise
Linux) et installer 2 paquets qui n'existent que dans EPEL.

C'est l'occasion d'utiliser **les options avancées** du module
`ansible.builtin.dnf` qui n'existent pas dans `ansible.builtin.package` :
`enablerepo`, `update_cache`, `exclude`.

### 🧩 Étapes

1. **Installer `epel-release`** (paquet officiel qui ajoute le repo EPEL à
   `/etc/yum.repos.d/`).
2. **Installer `htop` et `ncdu`** (deux outils EPEL) avec :
   - `enablerepo: epel` — active explicitement le repo (par sécurité, même
     s'il est déjà activé après `epel-release`).
   - `update_cache: true` — refresh du cache dnf avant l'install.
   - `exclude: kernel*` — protège contre une mise à jour kernel par effet de
     bord (un metapackage qui tirerait du kernel).

### 🧩 Squelette

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

### 🚀 Lancement

```bash
ansible-playbook labs/modules-paquets/dnf-options/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "rpm -q epel-release htop ncdu"
ansible db1.lab -m ansible.builtin.command -a "ls /etc/yum.repos.d/ | grep -i epel"
```

### 🧪 Validation automatisée

```bash
pytest -v labs/modules-paquets/dnf-options/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-paquets-dnf-options
```

### 💡 Pour aller plus loin

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
