# Un rôle, deux équipes, deux ports

## La situation

Le rôle `webserver` fonctionne, mais il fige le port 80. L'équipe base de données
veut maintenant ce même rôle sur **db1.lab**, en écoute sur **8080** : le port 80
est déjà pris par un agent de supervision. Un collègue a voulu éditer les tâches
du rôle ; vous refusez. Un rôle qu'il faut modifier pour le réutiliser n'est pas
un rôle, c'est une copie en sursis. Les réglages appartiennent à l'appelant, les
détails internes non.

Votre mission, depuis **control-node.lab** :

1. Déployer le rôle `webserver` sur **db1.lab** en **surchargeant** son port
   d'écoute à **8080** et ses worker connections à **2048**, depuis le playbook
   uniquement, sans toucher au rôle.
2. Injecter une page d'accueil personnalisée qui porte le nom de l'hôte ciblé.
3. Prouver que la surcharge a bien pris : le port ouvert dans firewalld et la
   configuration générée doivent afficher **8080**, pas la valeur livrée.
4. Établir quelles variables sont faites pour être surchargées et lesquelles
   sont des détails internes que l'appelant ne doit jamais atteindre.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/variables-defaults-vars/

## 🎯 Challenge — Override de variables au niveau du play

Vous avez vu le rôle `webserver` paramétré par `defaults/main.yml`. Le challenge consiste à **override** ces valeurs depuis un playbook qui appelle le rôle, et à **prouver** que les nouvelles valeurs sont bien appliquées.

### ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **`db1.lab`** uniquement.
2. Appelle le rôle `webserver` avec **3 variables overridées** :
   - `webserver_listen_port: 8080` (au lieu de 80)
   - `webserver_worker_connections: 2048` (au lieu de 1024)
   - `webserver_index_content: "Custom page from challenge lab 59 on {{ inventory_hostname }}"`

### 🧩 Consignes

Squelette à compléter (`challenge/solution.yml`) :

```yaml
---
- name: Challenge — override des defaults d'un rôle au niveau du play
  hosts: ???
  become: ???
  roles:
    - role: webserver
      vars:                              # vars du play : priorité 12
        webserver_listen_port: ???       # 8080
        webserver_worker_connections: ???    # 2048
        webserver_index_content: "{{ ??? }}"   # avec inventory_hostname
```

Lancement (note l'env var `ANSIBLE_ROLES_PATH`, pas `-e`) :

```bash
ANSIBLE_ROLES_PATH=labs/roles/variables-defaults-vars/roles \
ansible-playbook labs/roles/variables-defaults-vars/challenge/solution.yml
```

> 💡 **Pièges** :
>
> - **Précédence** : `vars/` du rôle (priorité 15) > `vars:` du play
>   (priorité 12) > `defaults/` du rôle (priorité 2). Si vous tentez
>   d'override `__webserver_html_dir` (défini dans `vars/main.yml`), ça
>   **ne marche pas**. Pour overrider, modifier le rôle ou utiliser
>   `--extra-vars` (priorité 22, top du top).
> - **`ANSIBLE_ROLES_PATH`** est une env var Ansible, **pas un `-e`** du
>   playbook. Le `-e ansible_roles_path=...` ne configure rien (c'est une
>   extra-var inutile au play).
> - **Variables avec `inventory_hostname`** : pensez à les poser entre
>   guillemets car `{{ }}` peut être interprété par YAML (`"{{ ... }}"`).

Vérifier sur `db1.lab` :

   ```bash
   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "sudo firewall-cmd --zone=public --list-ports"
   # → 8080/tcp doit apparaître

   ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "cat /usr/share/nginx/html/index.html"
   # → Custom page from challenge lab 59 on db1.lab
   ```

### 🧪 Validation

Le test pytest vérifie automatiquement :

- nginx installé.
- Service nginx running.
- Firewalld a le port **8080/tcp** ouvert (preuve que `webserver_listen_port=8080` est passé via le `vars:` du play, **pas** la valeur 80 des `defaults/`).
- Le fichier `/usr/share/nginx/html/index.html` contient le **custom message**.

```bash
pytest -v challenge/tests/
```

### 🚀 Pour aller plus loin

- Modifier `defaults/main.yml` du rôle pour mettre `webserver_listen_port: 80` (déjà la valeur par défaut). Re-lancer la solution. Le résultat est le **même** — preuve que **les `vars:` du play override les `defaults/`**.
- Tenter d'override `__webserver_html_dir` (qui est dans `vars/main.yml`). Observer que la valeur d'override **n'est pas prise en compte** — `vars/` (priorité 15) gagne sur `vars:` du play (priorité 12). Attention : un `vars:` posé sous `- role:` est un role param (priorité 20), lui GAGNE.
- Combiner `--extra-vars "webserver_listen_port=9999"` en CLI : cette valeur **gagne sur tout** (priorité 22, le top de la précédence).

---

Bonne chance ! 🧠

### 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean roles-variables-defaults-vars
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
