# 🎯 Challenge — nginx sur db1.lab, port 8888

Vous venez de déployer **nginx** sur les `webservers`, sur son port par défaut.
Le challenge consiste à réécrire un playbook qui fait la **même logique** sur
**db1.lab**, mais en exposant le service sur le **port 8888**.

C'est l'occasion d'appliquer ce que vous venez d'apprendre (modules idempotents,
ordre des tâches, ouverture firewalld) sur un autre hôte, et de découvrir que
changer un simple numéro de port fait apparaître un verrou de plus sur RHEL :
**SELinux**.

## ✅ Objectif

Écrire un playbook nommé `solution.yml` à la racine de **ce répertoire**
(`labs/premiers-pas/premier-playbook/challenge/solution.yml`) qui :

1. Cible l'hôte `db1.lab` (groupe `dbservers`)
2. Installe le paquet `nginx`
3. Démarre et active le service `nginx` au boot
4. **Configure nginx pour écouter sur le port `8888`** au lieu de 80
5. Fait accepter ce port par **SELinux**
6. Ouvre le port **8888** dans firewalld (zone publique)
7. Pose une page d'accueil `index.html` avec le texte exact :
   `Hello from db1.lab — Ansible RHCE 2026`

## 🧩 Consignes

Squelette à compléter (`challenge/solution.yml`) :

```yaml
---
- name: "Challenge : nginx sur db1, port 8888"
  hosts: ???
  become: ???
  tasks:
    - name: Installer nginx
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Forcer nginx à écouter sur 8888 (au lieu de 80)
      ansible.builtin.lineinfile:
        path: /etc/nginx/nginx.conf
        regexp: ???                  # matcher 'listen <port>;' quel que soit le port
        line: ???                    # attention à l'indentation dans le bloc server

    - name: Autoriser SELinux à laisser nginx écouter sur 8888
      community.general.seport:
        ports: ???
        proto: tcp
        setype: ???                  # http_port_t
        state: present

    - name: Ouvrir le port 8888 dans firewalld (zone publique, persistant + immédiat)
      ansible.posix.firewalld:
        port: ???
        permanent: ???
        immediate: ???
        state: ???

    - name: Poser la page d'accueil
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"

    - name: Démarrer et activer nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???
        enabled: ???
```

> 💡 **Pièges** :
>
> - **SELinux bloque les ports non standard** : sans la tâche
>   `community.general.seport`, nginx échoue à démarrer avec un
>   `bind() to 0.0.0.0:8888 failed (13: Permission denied)`. C'est l'erreur la
>   plus fréquente sur les premiers playbooks RHEL, et ouvrir le pare-feu n'y
>   change rien : ce sont **deux verrous distincts**.
> - **Quand ça échoue, montez la verbosité** : `ansible-playbook -vvv` affiche
>   les arguments du module et le retour brut, ce qui suffit le plus souvent à
>   voir ce que la cible a réellement reçu. Le lab `troubleshooting/verbosite`
>   traite ce point et les plugins de callback ; inutile d'attendre d'y être.
> - **Vous n'avez pas à maîtriser SELinux ici** : la tâche ci-dessus suffit
>   pour réussir. SELinux a son propre lab plus loin (`modules-rhel/selinux`),
>   où les booléens, les contextes de fichiers et `semanage` sont vus
>   correctement. Le rencontrer si tôt est volontaire : sur RHEL, on bute
>   dessus dès son premier vrai playbook.
> - **Pourquoi 8888 et pas 8080** : sur RHEL, nginx tourne dans le domaine
>   SELinux `httpd_t`, que la politique autorise déjà sur `http_cache_port_t`,
>   dont fait partie 8080. Sur 8080, la tâche `seport` ne servirait donc à
>   rien, et vous n'auriez rien appris. Sur 8888, elle est indispensable.
>   Vérifiez vous-même :
>   `semanage port -l | grep -E '^http_(port|cache_port)_t'`.
> - **Ordre des tâches** : posez la page d'accueil **avant** de démarrer
>   nginx, sinon le premier `curl` peut tomber sur la page par défaut.
> - **`firewalld`** : `permanent: true` + `immediate: true` ensemble
>   garantissent règle persistante + active sans `--reload`.
> - Le fichier de page d'accueil est `/usr/share/nginx/html/index.html`, le
>   docroot par défaut de nginx sur RHEL. Ce n'est **pas** `/var/www/html`,
>   qui est celui d'Apache.

Lancez votre solution depuis la **racine du repo** :

```bash
ansible-playbook labs/premiers-pas/premier-playbook/challenge/solution.yml
```

Puis testez :

```bash
curl http://db1.lab:8888
# Doit retourner : Hello from db1.lab — Ansible RHCE 2026
```

## 🧪 Validation

Le script `tests/test_functional.py` valide automatiquement votre solution.
Il vérifie sur **db1.lab** :

- Le paquet `nginx` est **installed**
- Le service `nginx` est **running** et **enabled**
- Le port **8888** est en **listening**
- Le port **8888** porte l'étiquette SELinux `http_port_t` (preuve de `seport`)
- Le port **8888** est ouvert dans firewalld (zone publique)
- La requête HTTP `http://db1.lab:8888` retourne **200**
- Le **contenu** de la page est exactement
  `Hello from db1.lab — Ansible RHCE 2026`
- La solution est **idempotente** : un second passage n'annonce aucun changement (critère RHCE)

Pour lancer les tests, depuis la racine du repo :

```bash
pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez une **vérification finale** dans votre playbook avec
  `ansible.builtin.uri` qui appelle `http://localhost:8888` côté managed node et
  vérifie que le code HTTP retourné est `200` et que le `content` correspond.
- Retirez la tâche `seport`, lancez
  `sudo semanage port -d -t http_port_t -p tcp 8888` sur db1, puis relancez le
  playbook et lisez le message d'erreur de nginx. C'est celui que vous
  rencontrerez en production : apprenez à le reconnaître.
- Refaites le challenge en utilisant un **template Jinja2** au lieu d'une copie
  de contenu en dur (anticipation de la section `ecrire-code/`).

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean premiers-pas-premier-playbook
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
