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

1. Créez le fichier `challenge/solution.yml` (vide pour démarrer).
2. Reprenez le squelette d'un play : `name`, `hosts: db1.lab`, `become: true`,
   `tasks:`.
3. Pour **forcer httpd à écouter sur 8080**, vous devez modifier
   `/etc/httpd/conf/httpd.conf`. Indices :

   - Le module **`ansible.builtin.lineinfile`** remplace la ligne
     `Listen 80` par `Listen 8080`.
   - Pensez au paramètre **`regexp:`** pour matcher la ligne existante.
   - SELinux **bloque httpd sur les ports non-standard** par défaut. Le module
     **`community.general.seport`** autorise le port 8080 sur le type
     `http_port_t`. Sinon, httpd ne pourra pas démarrer.

4. Pour la **page d'accueil**, le module **`ansible.builtin.copy`** avec
   `content:` permet de poser le contenu directement sans fichier source.
5. Lancez votre solution depuis la **racine du repo** :

   ```bash
   ansible-playbook labs/premiers-pas/premier-playbook/challenge/solution.yml
   ```

6. Vérifiez le résultat depuis le control node :

   ```bash
   curl http://db1.lab:8080
   ```

   Le `curl` doit retourner exactement :
   `Hello from db1.lab — Ansible RHCE 2026`.

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
