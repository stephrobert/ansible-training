# Lab 99 — Rôles système RHEL : converger l'heure avec `timesync`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis unique : les 4 VMs du lab répondent au ping.

## 🧠 Rappel

🔗 [**Les rôles Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/)

« **Use RHEL system roles** » est un objectif explicite de l'examen **EX294**.
C'est le seul objectif de l'examen que cette formation n'abordait nulle part
avant ce lab.

Un **rôle système** est un rôle écrit et maintenu par Red Hat, livré avec la
distribution, qui expose une **interface stable de variables** au-dessus d'un
sous-système dont la configuration change d'une version à l'autre. Vous ne
décrivez plus un fichier, vous décrivez un **résultat** :

```yaml
- name: Converger l'heure
  hosts: db1.lab
  become: true
  vars:
    timesync_ntp_servers:
      - hostname: 0.fr.pool.ntp.org
        iburst: true
  roles:
    - role: fedora.linux_system_roles.timesync
```

Le rôle se charge du reste : détecter si la machine tourne sous `chrony` ou
`ntpd`, installer le paquet, générer le fichier, désactiver le fournisseur
concurrent, redémarrer le démon. Le même play vaut de RHEL 6 à RHEL 10.

## 📦 Paquet ou collection ? Les deux, et ce n'est pas la même chose

Il existe **deux distributions du même code** (le projet upstream
[linux-system-roles](https://linux-system-roles.github.io/)) :

| | Paquet `rhel-system-roles` | Collection `fedora.linux_system_roles` |
| --- | --- | --- |
| Origine | dépôt `appstream` de RHEL / AlmaLinux | Ansible Galaxy |
| Installation | `dnf install rhel-system-roles` | `ansible-galaxy collection install` |
| Emplacement | `/usr/share/ansible/roles/` et `/usr/share/ansible/collections/` | `~/.ansible/collections/` |
| Nom d'appel | `redhat.rhel_system_roles.timesync` | `fedora.linux_system_roles.timesync` |
| Support | certifié Red Hat | communautaire |
| **Le jour de l'examen** | **c'est celui-là** | absent |

**Ce lab utilise la collection.** Deux raisons, mesurables :

1. **Le paquet n'est pas installable sur le nœud de contrôle de cette
   formation.** Un rôle est résolu **là où tourne `ansible-playbook`**, jamais
   sur la cible. Ici, `ansible-playbook` tourne sur votre poste (Ubuntu dans le
   harnais de tests), qui n'a ni `dnf` ni `rpm` : `/usr/share/ansible/roles/`
   n'y existera jamais. Le paquet **est** disponible pour AlmaLinux
   (`dnf list --available rhel-system-roles` sur db1.lab rend la version
   1.120.5), mais il ne servirait qu'à un nœud de contrôle RHEL.
2. **C'est le même code.** La collection installée ici est en 1.121.0, le paquet
   AlmaLinux en 1.120.5 : deux empaquetages du même upstream, à une version
   mineure près.

> ⚠️ **Le jour de l'examen**, le nœud de contrôle est un RHEL. Le réflexe est
> `dnf install rhel-system-roles`, puis `redhat.rhel_system_roles.<role>`.
> **Seul le préfixe change**, les variables sont identiques. Ce que vous
> apprenez ici se transpose tel quel.

Vérifiez ce dont vous disposez :

```bash
ansible-galaxy collection list fedora.linux_system_roles
ls ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/
```

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Trouver** les rôles système disponibles et **lire** leur interface
   (`defaults/main.yml`, `README.md` du rôle).
2. **Consommer** un rôle système en **FQCN** depuis un play.
3. Piloter `chronyd` **par variables** (`timesync_ntp_servers`,
   `timesync_step_threshold`, `timesync_min_sources`) sans jamais toucher
   `/etc/chrony.conf`.
4. **Prouver** que la configuration est appliquée, en interrogeant le démon et
   pas le fichier.
5. Faire la différence entre le **paquet** et la **collection**, et savoir
   lequel vous attend à l'examen.

## 🔧 Préparation

```bash
ansible db1.lab -m ansible.builtin.ping
```

## 📚 Exercice 1 — L'interface du rôle, avant le rôle

Un rôle système se lit par ses **defaults** : ce sont ses paramètres publics.

```bash
cat ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/timesync/defaults/main.yml
```

```yaml
timesync_ntp_servers: []
timesync_ptp_domains: []
timesync_dhcp_ntp_servers: false
timesync_step_threshold: -1.0
timesync_min_sources: 1
timesync_ntp_provider: ""
```

🔍 **Observations** :

- **Toutes les variables sont préfixées `timesync_`.** C'est la règle des rôles
  système, et la raison pour laquelle on peut en empiler dix dans un play sans
  collision.
- **`timesync_ntp_provider: ""`** : vide veut dire « débrouille-toi ». Le rôle
  détecte `chrony` ou `ntpd` selon ce qui est installé.
- **`timesync_ntp_servers: []`** : une **liste de dictionnaires**, pas de
  chaînes. Chaque entrée porte un `hostname` et ses options.

## 📚 Exercice 2 — L'état de départ de db1

```bash
ssh db1.lab
sudo grep -vE '^\s*(#|$)' /etc/chrony.conf
```

```text
pool 2.almalinux.pool.ntp.org iburst
sourcedir /run/chrony-dhcp
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
ntsdumpdir /var/lib/chrony
logdir /var/log/chrony
```

🔍 **Observations** :

- Un **`pool`** (une seule ligne, quatre sources derrière) et pas des `server`.
- **`sourcedir /run/chrony-dhcp`** : le client DHCP peut injecter ses propres
  serveurs NTP. Pour un serveur de conformité, c'est une porte ouverte.
- **`makestep 1.0 3`** et **pas de `minsources`** : ce sont les valeurs de la
  distribution, pas les vôtres.

> ⚠️ **Le piège du fichier livré** : `/etc/chrony.conf` contient la ligne
> `#minsources 2`, **en commentaire**. Un test qui chercherait la sous-chaîne
> `minsources 2` dans le fichier serait vert avant même que vous ayez commencé.
> Les tests de ce lab ne comparent que des **lignes actives**, par égalité.

## 📚 Exercice 3 — Une entrée de `timesync_ntp_servers`

```yaml
timesync_ntp_servers:
  - hostname: 2.fr.pool.ntp.org
    iburst: true
    maxpoll: 10
```

devient, dans `/etc/chrony.conf` :

```text
server 2.fr.pool.ntp.org maxpoll 10 iburst
```

🔍 **Observation, et elle est le cœur du lab** : **l'ordre des options de la
ligne générée n'est pas celui de votre dictionnaire.** Le template du rôle les
émet dans son ordre à lui (`minpoll`, `maxpoll`, `nts`, `iburst`, `prefer`…).
Vous décrivez une **intention** ; la syntaxe est le problème du rôle. C'est
précisément ce qu'on achète en utilisant un rôle système, et c'est pourquoi
recopier le résultat à la main est un contresens.

Clés utiles d'une entrée : `hostname` (requis), `iburst`, `prefer`, `minpoll`,
`maxpoll`, `pool` (émet `pool` au lieu de `server`), `nts`, `trust`.

## 📚 Exercice 4 — Ce que le rôle fait en plus du fichier

Lancez le play du challenge, puis comparez :

```bash
ssh db1.lab
sudo head -4 /etc/chrony.conf        # la signature du rôle
sudo cat /etc/sysconfig/network      # PEERNTP=no
chronyc -N sources                   # ce que le démon a VRAIMENT chargé
```

🔍 **Trois effets qu'on oublie systématiquement quand on écrit le fichier à la
main** :

1. **La signature.** Le rôle ouvre le fichier par `# Ansible managed` puis
   `# system_role:timesync`. C'est ce qui dit à l'admin suivant de ne pas
   éditer ce fichier.
2. **`PEERNTP=no`** dans `/etc/sysconfig/network`. Sans lui, le client DHCP
   réinjecte ses serveurs au prochain bail et votre conformité saute en
   silence, des semaines plus tard.
3. **Le redémarrage.** Le rôle **notifie un handler** `Restart chronyd`.
   Un fichier écrit sans redémarrage ne change rien : `chronyd` tourne toujours
   sur l'ancienne configuration, et `chronyc` vous le dira.

> 💡 **`chronyc` interroge le démon, pas le disque.** C'est l'outil qui
> distingue « j'ai écrit un fichier » de « la machine est configurée ».

## 🔍 Observations à noter

- Un rôle système est **idempotent par construction** : rejoué, il ne réécrit
  pas le fichier et ne redémarre pas le démon. Vérifiez-le, c'est un critère
  RHCE.
- **`gather_facts: true`** n'est pas indispensable (le rôle collecte lui-même
  les facts dont il a besoin), mais restez sur le réflexe de l'examen.
- **Ne définissez jamais une variable `timesync_*` que vous n'avez pas lue**
  dans `defaults/main.yml` ou dans le `README.md` du rôle : ce qui n'est pas
  dans l'interface est privé et peut changer sans préavis.

## 🤔 Questions de réflexion

1. Vous mettez `timesync_ntp_provider: ntp` sur une machine où seul `chrony`
   est installé. Que fait le rôle ? (Indice : lisez la tâche `Install ntp`.)
2. Pourquoi le rôle écrit-il `PEERNTP=no` alors que vous ne le lui avez pas
   demandé ? Quelle variable le remettrait à `yes` ?
3. Vous devez appliquer `timesync` à 200 machines dont 40 sont des RHEL 7.
   Qu'est-ce que le rôle vous évite d'écrire ?
4. Le jour de l'examen, `dnf install rhel-system-roles` puis
   `ansible-galaxy collection list` : à quel endroit du système de fichiers le
   paquet a-t-il posé la collection, et pourquoi Ansible la trouve-t-il sans
   configuration ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **Les autres rôles de l'examen** : `firewall`, `selinux`, `storage`,
  `postfix`, `sshd`. Tous suivent la même grammaire : préfixe de variables,
  `defaults/main.yml` comme contrat, idempotence.
- **`ansible-doc -t role -l fedora.linux_system_roles`** : la liste des rôles
  avec leur description, sans quitter le terminal.
- **`timesync_ntp_ip_family: IPv4`** : force `-4` dans les options de `chronyd`.
  Regardez ce que devient `/etc/sysconfig/chronyd`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile production labs/roles/system-roles/
```
