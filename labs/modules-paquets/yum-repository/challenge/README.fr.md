# Challenge `yum_repository:`

## Énoncé

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

## Critères de réussite

- `/etc/yum.repos.d/epel.repo` existe et contient `enabled = 1`.
- `rpm -q htop` retourne le nom + version du paquet.
- `/etc/yum.repos.d/local-test.repo` existe et contient `enabled = 0`.
- `dnf repolist enabled | grep local-test` ne retourne **rien**.
- 2e run du playbook : `changed: 0`.

## Indices

- L'ordre compte : la clé GPG doit être importée **avant** de déclarer le
  dépôt qui l'exige, et le dépôt déclaré **avant** d'installer le paquet.
- Le paramètre `name` du dépôt détermine le nom du fichier `.repo` généré
  dans `/etc/yum.repos.d/`.
- Les macros `$releasever` et `$basearch` (ou la variable de facts
  `ansible_distribution_major_version`) évitent de figer la version.
- Désactiver n'est pas supprimer : un dépôt désactivé reste déclaré,
  `dnf repolist all` le montre encore, `dnf repolist enabled` non.
