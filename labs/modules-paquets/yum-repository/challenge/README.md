# Challenge `yum_repository:`

## Énoncé

Sur une VM **RHEL/AlmaLinux/Rocky 9** (`db1.lab` ou autre), écrivez
`solution.yml` qui :

1. Importe la clé GPG **Docker CE** (`https://download.docker.com/linux/centos/gpg`).
2. Déclare le dépôt **Docker CE** avec `gpgcheck: true` et `repo_gpgcheck: true`.
3. Installe le paquet **`docker-ce`** depuis ce dépôt.
4. Désactive ensuite le dépôt (`enabled: false`) sans le supprimer.
5. Vérifie via `command: dnf repolist enabled` que `docker-ce` n'apparaît plus.

## Critères de réussite

- `docker-ce` installé : `rpm -q docker-ce` retourne le nom + version.
- `dnf repolist enabled | grep docker-ce` ne retourne **rien** après
  désactivation.
- Le fichier `/etc/yum.repos.d/docker-ce.repo` existe toujours mais
  contient `enabled=0`.

## Indices

- L'ordre `rpm_key:` AVANT `yum_repository:` AVANT `dnf:` est mandatory.
- Pour vérifier qu'un dépôt est désactivé, `dnf repolist all` (vs `dnf repolist enabled`).
