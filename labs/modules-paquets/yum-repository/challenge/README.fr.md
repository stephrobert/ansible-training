# Ouvrir EPEL sous signature, préparer le dépôt local fermé

## La situation

L'équipe supervision a besoin de `htop` sur **db1.lab**, et les dépôts de
base ne le fournissent pas : il vit dans **EPEL**. La politique de sécurité
est explicite : rien ne s'installe depuis une source non signée, le dépôt
entre donc avec sa clé GPG importée et la vérification de signature active.
Pendant ce temps, l'équipe build prépare un dépôt RPM interne servi depuis
le disque local ; il doit être **déclaré dès maintenant mais rester fermé**
tant que son contenu n'est pas validé, car un dépôt déclaré et activé
s'invite en silence dans chaque futur `dnf update`. Le tout piloté depuis
**control-node.lab**, et rejouable sans le moindre changement au second
passage.

Votre mission :

1. Importer la **clé GPG EPEL** sur **db1.lab**, puis déclarer le dépôt EPEL
   correspondant à la version de la distribution, **activé et vérifié par
   signature**.
2. Installer **`htop`** depuis ce dépôt.
3. Déclarer le dépôt **`local-test`** (`file:///srv/repo/`), **désactivé** :
   le fichier `.repo` existe sur le disque, le dépôt ne sert jamais.
4. Le prouver : le paquet est installé, EPEL apparaît parmi les dépôts
   actifs, `local-test` reste hors de la liste des dépôts activés, et un
   second passage affiche `changed: 0`.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/

## Challenge `yum_repository:`

### Énoncé

Sur **db1.lab** (AlmaLinux 9), écrivez `solution.yml` qui amène la machine
dans cet état :

1. Le dépôt **EPEL** correspondant à la version de la distribution est
   déclaré dans `/etc/yum.repos.d/epel.repo`, **activé** et avec la
   **vérification GPG obligatoire** (clé importée, `gpgcheck` actif).
   Les URLs officielles :
   - baseurl : `https://dl.fedoraproject.org/pub/epel/<version>/Everything/$basearch/`
   - clé GPG : `https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-<version>`
2. Le paquet **`htop`** (fourni par EPEL, absent des dépôts de base) est
   **installé**.
3. Un dépôt **`local-test`** est déclaré dans
   `/etc/yum.repos.d/local-test.repo`, baseurl `file:///srv/repo/`,
   **présent mais désactivé** : le fichier existe, le dépôt ne sert jamais.
4. Un 2e run du playbook ne change rien (idempotent).

### Critères de réussite

- `/etc/yum.repos.d/epel.repo` existe et contient `enabled = 1`.
- `rpm -q htop` retourne le nom + version du paquet.
- `/etc/yum.repos.d/local-test.repo` existe et contient `enabled = 0`.
- `dnf repolist enabled | grep local-test` ne retourne **rien**.
- 2e run du playbook : `changed: 0`.

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-paquets-yum-repository
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.
