# Le rôle part en public et ne connaît que RHEL

## La situation

Votre rôle `webserver` va être publié, et la première issue est déjà prévisible.
Il appelle `dnf` en direct, écrit dans `/usr/share/nginx/html` et suppose que le
service tourne sous l'utilisateur `nginx`. Sur Debian, le gestionnaire de paquets
est faux, la racine web est ailleurs et l'utilisateur s'appelle `www-data`. Le
rôle ne fonctionne nulle part ailleurs, et pire : la suite de tests n'a aucun
moyen de s'en apercevoir, elle n'a jamais testé que la distribution de l'auteur.

Votre mission, depuis le répertoire du projet :

1. Étendre la matrice de test à **trois distributions** couvrant au moins deux
   familles d'OS, pour que la suite échoue le jour où la portabilité casse.
2. Sortir des tâches les faits divergents (nom du paquet, racine web,
   utilisateur du service) vers des **fichiers de variables par OS**, chargés
   d'après la famille détectée sur la cible.
3. Remplacer les appels de paquets spécifiques par le module **agnostique**,
   pour que le rôle cesse de choisir le gestionnaire à la place de l'appelant.
4. Vérifier que le **même** rôle, inchangé, converge sur les trois plateformes.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-scenarios-multi-distro/

## 🎯 Challenge : rendre le rôle webserver réellement multi-distro

### ✅ Mission

Le rôle `webserver` est livré **mono-distro** : `dnf` en dur, chemins et
utilisateur RHEL en dur. Il échoue sur Debian. Votre travail : le rendre
portable RHEL + Debian **sans dupliquer les tâches**, et prouver la
portabilité avec une matrice Molecule.

État attendu (c'est ce que pytest vérifie) :

| Élément | Attente |
| --- | --- |
| `tasks/main.yml` | `include_vars` dynamique basé sur `ansible_os_family` ; module agnostique `ansible.builtin.package` (plus aucun `dnf:`/`apt:`) ; plus aucun chemin ni user codé en dur (variables `__webserver_*`) |
| `vars/RedHat.yml` | complété : paquet, service, répertoire HTML et user de la famille RedHat |
| `vars/Debian.yml` | complété : mêmes clés, valeurs propres à Debian (répertoire HTML et user DIFFÉRENTS de RHEL) |
| `molecule.yml` | au moins 3 plateformes couvrant les deux familles |
| Le tout | `molecule syntax` passe (pytest l'exécute réellement) |

### 🧩 Bloqué ?

```bash
dsoxlab hint molecule-scenarios-multi-distro
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées. Ce journal
doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/scenarios-multi-distro/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-scenarios-multi-distro
```

### 💡 Pour aller plus loin

- Ajoutez ubuntu2404 à la matrice : que faut-il changer dans le rôle ?
  (Réponse attendue : rien, c'est le but.)
- `vars/{{ ansible_distribution }}.yml` en surcharge fine de
  `{{ ansible_os_family }}.yml` : le pattern first_found.
