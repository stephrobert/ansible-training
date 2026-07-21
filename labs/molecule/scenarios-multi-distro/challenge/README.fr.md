# 🎯 Challenge : rendre le rôle webserver réellement multi-distro

## ✅ Mission

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

## 🧩 Indices

- Le chargement dynamique s'écrit :

  ```yaml
  - name: Charger les variables de la distribution
    ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"
  ```

- `ansible.builtin.package` délègue au gestionnaire natif (dnf ou apt) :
  une seule tâche d'installation pour toutes les familles.
- Sur Debian, nginx sert `/var/www/html` et tourne sous `www-data` ; sur
  RHEL, `/usr/share/nginx/html` et `nginx`. C'est exactement ce que vos
  deux fichiers vars doivent capturer.
- Preuve finale multi-distro (Podman requis) :

  ```bash
  cd labs/molecule/scenarios-multi-distro
  ANSIBLE_ROLES_PATH=$PWD/roles molecule test
  ```

  Trois instances montent en parallèle et le même rôle s'adapte à chacune.

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées. Ce journal
doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/scenarios-multi-distro/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean molecule-scenarios-multi-distro
```

## 💡 Pour aller plus loin

- Ajoutez ubuntu2404 à la matrice : que faut-il changer dans le rôle ?
  (Réponse attendue : rien, c'est le but.)
- `vars/{{ ansible_distribution }}.yml` en surcharge fine de
  `{{ ansible_os_family }}.yml` : le pattern first_found.
