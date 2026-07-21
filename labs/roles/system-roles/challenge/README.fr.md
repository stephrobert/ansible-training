# 🎯 Challenge — Piloter `chronyd` par le rôle système `timesync`

## ✅ Objectif

Écrire `challenge/solution.yml` : **un play** sur db1.lab qui consomme le rôle
système **`fedora.linux_system_roles.timesync`** et lui passe l'intention de
conformité en variables.

Les tests ne relisent pas votre configuration : ils vérifient l'**état de
db1.lab**, y compris ce que `chronyd` a réellement chargé **en mémoire**. Un
fichier correct sur le disque avec un démon qui tourne encore sur l'ancienne
configuration est un échec.

> ⚠️ **Le seul interdit du lab** : n'écrivez pas `/etc/chrony.conf` vous-même.
> Ni `copy`, ni `template`, ni `lineinfile`, ni `blockinfile`. Tout passe par
> les variables du rôle. Un test parse votre YAML et exige le rôle en FQCN dans
> la liste `roles:` du play.

## 🧩 Contrat attendu

### Les trois serveurs NTP

| Serveur | Options demandées |
| --- | --- |
| `0.fr.pool.ntp.org` | `iburst`, **source préférée** |
| `1.fr.pool.ntp.org` | `iburst` |
| `2.fr.pool.ntp.org` | `iburst`, **intervalle d'interrogation maximal de 10** |

Rappel : chaque entrée de `timesync_ntp_servers` est un **dictionnaire**, dont
la seule clé requise est `hostname`. Les autres options sont des booléens ou des
entiers portant le nom de la directive chrony correspondante.

### Les deux réglages d'horloge

- **Seuil de correction brutale** : `0.1` seconde (la distribution est à `1.0`).
- **Minimum de sources concordantes** avant ajustement : `2` (la distribution
  est à `1`).

### Ce qui doit disparaître

- La directive **`pool`** de la distribution.
- La directive **`sourcedir`**, qui laissait le DHCP injecter ses serveurs.

Ces deux-là partent **toutes seules** si vous avez fait le reste correctement :
le rôle **régénère** le fichier au lieu de l'amender. Si elles sont encore là,
c'est que quelque chose écrit à côté du rôle.

## 🧩 Squelette

```yaml
---
- name: Converger la synchronisation horaire de db1
  hosts: ???
  become: true
  gather_facts: true
  vars:
    timesync_ntp_servers:
      - hostname: ???
        iburst: ???
        ???: true
      - hostname: ???
        iburst: ???
      - hostname: ???
        iburst: ???
        ???: 10
    timesync_step_threshold: ???
    timesync_min_sources: ???
  roles:
    - role: ???
```

> 💡 **Pièges** :
>
> - **Le FQCN.** `timesync` tout court ne résout pas : le rôle vit dans une
>   collection. C'est `fedora.linux_system_roles.timesync`. Le jour de
>   l'examen, sur un nœud de contrôle RHEL, ce sera
>   `redhat.rhel_system_roles.timesync` : même rôle, même variables, autre
>   empaquetage.
> - **Le nom des options.** Elles ne s'inventent pas. Elles sont dans
>   `defaults/main.yml` et dans le `README.md` du rôle :
>   `ls ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/timesync/`
> - **Le redémarrage n'est pas votre affaire.** Le rôle notifie son propre
>   handler. Si vous ajoutez un `systemd_service: state=restarted` « pour être
>   sûr », votre play ne sera plus idempotent et le test d'idempotence le dira.
> - **`0.1` n'est pas `"0.1"`.** Le seuil est un flottant.

## 🚀 Lancement

```bash
ansible-playbook labs/roles/system-roles/challenge/solution.yml
```

## 🧪 Validation

```bash
pytest -v labs/roles/system-roles/challenge/tests/
```

Pour voir de vos yeux ce que les tests regardent :

```bash
ssh db1.lab
sudo grep -vE '^\s*(#|$)' /etc/chrony.conf   # les directives actives
sudo cat /etc/sysconfig/network              # PEERNTP=no
chronyc -N sources                           # ce que le démon a chargé
chronyc tracking                             # sur quoi l'horloge est verrouillée
```

## 🧹 Reset

```bash
dsoxlab clean roles-system-roles
```

## 💡 Pour aller plus loin

- **Passez `timesync_dhcp_ntp_servers: true`** et rejouez : `sourcedir`
  réapparaît, `PEERNTP=no` disparaît. Une variable, deux fichiers, zéro ligne
  de configuration écrite.
- **Retirez `timesync_min_sources`** et rejouez : la directive `minsources`
  disparaît du fichier. Le rôle ne laisse pas de résidu de votre run précédent,
  contrairement à un `lineinfile`.
- **`ansible-playbook --check --diff`** : le rôle affiche le diff du fichier
  qu'il *aurait* écrit. C'est la revue de configuration que vous ne pouvez pas
  faire avec un `copy` de contenu inline.
- **`ansible-lint --profile production labs/roles/system-roles/challenge/solution.yml`** :
  sortie attendue `Passed: 0 failure(s), 0 warning(s)`.
