# 🎯 Challenge — Apache (httpd) sur db1.lab, port 8080

Vous venez de déployer **nginx** sur les `webservers`. Le challenge consiste à
réécrire un playbook qui fait la **même logique** mais avec **Apache (httpd)** sur
**db1.lab**, en exposant le service sur le **port 8080**.

C'est l'occasion d'appliquer ce que vous venez d'apprendre — modules idempotents,
ordre des tâches, ouverture firewalld — sur un autre service, et de réaliser que la
**structure d'un playbook reste la même** quel que soit le logiciel déployé.

## ✅ Objectif

Écrire un playbook nommé `solution.yml` à la racine de **ce répertoire**
(`labs/premiers-pas/premier-playbook/challenge/solution.yml`) qui :

1. Cible l'hôte `db1.lab` (groupe `dbservers`)
2. Installe le paquet `httpd`
3. Démarre et active le service `httpd` au boot
4. **Configure httpd pour écouter sur le port `8080`** au lieu de 80
5. Ouvre le port **8080** dans firewalld (zone publique)
6. Pose une page d'accueil `index.html` avec le texte exact :
   `Hello from db1.lab — Ansible RHCE 2026`

## 🧩 Consignes

Squelette à compléter (`challenge/solution.yml`) :

```yaml
---
- name: Challenge — Apache sur db1, port 8080
  hosts: ???
  become: ???
  tasks:
    - name: Installer httpd
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Forcer httpd à écouter sur 8080 (au lieu de 80)
      ansible.builtin.lineinfile:
        path: /etc/httpd/conf/httpd.conf
        regexp: ???                  # matcher 'Listen 80' (en début de ligne, espaces après)
        line: ???

    - name: Autoriser SELinux à laisser httpd écouter sur 8080
      community.general.seport:
        ports: ???
        proto: tcp
        setype: ???                  # http_port_t
        state: present

    - name: Ouvrir le port 8080 dans firewalld (zone publique, persistant + immédiat)
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

    - name: Démarrer et activer httpd
      ansible.builtin.systemd_service:
        name: httpd
        state: ???
        enabled: ???
```

> 💡 **Pièges** :
>
> - **SELinux bloque les ports non-standard** : sans la tâche
>   `community.general.seport`, httpd échoue à démarrer avec un cryptique
>   *"Permission denied"* dans les logs. C'est l'erreur la plus fréquente
>   sur les premiers playbooks RHEL.
> - **Ordre des tâches** : posez la page d'accueil **avant** de démarrer
>   httpd, sinon le premier `curl` peut tomber sur la page de bienvenue.
> - **`firewalld`** : `permanent: true` + `immediate: true` ensemble
>   garantissent règle persistante + active sans `--reload`.
> - Le fichier de page d'accueil est généralement `/var/www/html/index.html`
>   (DocumentRoot par défaut d'httpd RHEL).

Lancez votre solution depuis la **racine du repo** :

```bash
ansible-playbook labs/premiers-pas/premier-playbook/challenge/solution.yml
```

Puis testez :

```bash
curl http://db1.lab:8080
# Doit retourner : Hello from db1.lab — Ansible RHCE 2026
```

## 🧪 Validation

Le script `tests/test_premier_playbook.py` valide automatiquement votre solution.
Il vérifie sur **db1.lab** :

- Le paquet `httpd` est **installed**
- Le service `httpd` est **running** et **enabled**
- Le port **8080** est en **listening** sur l'interface 0.0.0.0
- Le port **8080** est ouvert dans firewalld (zone publique)
- La requête HTTP `http://db1.lab:8080` retourne **200**
- Le **contenu** de la page est exactement
  `Hello from db1.lab — Ansible RHCE 2026`

Pour lancer les tests, depuis la racine du repo :

```bash
pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez une **vérification finale** dans votre playbook avec
  `ansible.builtin.uri` qui appelle `http://localhost:8080` côté managed node et
  vérifie que le code HTTP retourné est `200` et que le `content` correspond.
- Refaites le challenge en utilisant un **template Jinja2** au lieu d'une copie
  de contenu en dur (anticipation de la section `ecrire-code/`).
- Étendez le challenge : déployez le même service sur `web1.lab` et `web2.lab`
  (au lieu de `db1.lab`) en utilisant un pattern d'hôtes — le test devra alors
  être adapté.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/premiers-pas/premier-playbook/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
