# 🎯 Challenge — Play complet sur db1 avec httpd

Vous avez écrit un play complet avec `pre_tasks` / `tasks` / `post_tasks` / `handlers`. Le challenge **reproduit ce pattern** sur un autre hôte (`db1.lab`) et un autre service (Apache `httpd` au lieu de nginx) pour vérifier que vous maîtrisez l'**anatomie d'un play professionnel**.

> Les concepts de **parallélisme** (`serial:`, `max_fail_percentage:`, `strategy:`) sont l'objet du [lab 09](../../09-ecrire-code-parallelisme-strategies/) — ils ne sont **pas** demandés ici.

## ✅ Objectif

Écrire `solution.yml` à la racine de **ce répertoire**
(`labs/ecrire-code/plays-et-tasks/challenge/solution.yml`) qui :

1. Cible **un seul hôte** : `db1.lab` (groupe `dbservers`)
2. Utilise **`pre_tasks` + `tasks` + `post_tasks` + `handlers`** comme dans l'exercice principal
3. Pose un fichier marqueur `/tmp/challenge-predeploy-db1.txt` dans `pre_tasks`
4. Installe `httpd` (Apache) + le démarre + l'active
5. Modifie `/etc/httpd/conf.d/welcome.conf` pour qu'Apache renvoie `Challenge OK from db1.lab` (plutôt que la page par défaut)
6. **Notifie** le handler `Restart httpd` quand `welcome.conf` est modifié
7. Le handler redémarre httpd via `ansible.builtin.systemd state: restarted`
8. Pose un fichier marqueur `/tmp/challenge-postdeploy-db1.txt` dans `post_tasks`

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: Challenge — play complet sur db1 avec httpd
  hosts: ???
  become: ???
  pre_tasks:
    - name: Marqueur predeploy
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-predeploy-db1.txt
        content: "{{ inventory_hostname }} predeploy at {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"

  tasks:
    - name: Installer httpd
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Démarrer + activer httpd
      ansible.builtin.systemd_service:
        name: httpd
        state: ???
        enabled: ???

    - name: Poser la page d'accueil custom
      ansible.builtin.copy:
        dest: ???                          # /var/www/html/index.html
        content: "Challenge OK from {{ ??? }}\n"
        mode: "0644"
      notify: Restart httpd

  post_tasks:
    - name: Marqueur postdeploy (timestamp pour prouver l'ordre)
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-postdeploy-db1.txt
        content: "{{ inventory_hostname }} postdeploy at {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"

  handlers:
    - name: Restart httpd
      ansible.builtin.systemd_service:
        name: httpd
        state: ???                         # restarted
```

> 💡 **Pièges** :
>
> - **Ordre d'exécution** : `pre_tasks` → `tasks` → handlers (notifiés) →
>   `post_tasks`. Si vous mettez le marqueur predeploy dans `tasks:`, le
>   test `mtime predeploy < postdeploy` peut échouer.
> - **Idempotence du timestamp** : `ansible_date_time.iso8601` change à
>   chaque run → `copy:` détecte un diff et écrit. Au second run le
>   `changed=1` pour ces tâches est **attendu**, ce n'est pas un bug.
> - **Le test cherche** `Challenge OK from db1.lab` exactement (avec le
>   FQDN). Utilisez `inventory_hostname`, pas `ansible_hostname` (qui est
>   le hostname court).
> - **`welcome.conf`** : sur AlmaLinux 10, ce fichier intercepte la racine
>   `/`. Le plus propre est de le **supprimer** ou de poser un
>   `index.html` à la place.

Lancez la solution depuis la **racine du repo** :

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/challenge/solution.yml
```

Puis testez :

```bash
curl http://db1.lab
```

Le `curl` doit retourner exactement : `Challenge OK from db1.lab`

## 🧪 Validation

Le script `tests/test_plays_et_tasks.py` vérifie automatiquement :

- Le fichier `/tmp/challenge-predeploy-db1.txt` existe sur `db1.lab` et contient le hostname
- Le paquet `httpd` est installé
- Le service `httpd` est `running` et `enabled`
- Le port `80` est en `listening`
- Le port `80` est ouvert dans firewalld (zone publique)
- La requête HTTP `http://db1.lab` retourne **200** et contient `Challenge OK from db1.lab`
- Le fichier `/tmp/challenge-postdeploy-db1.txt` existe et contient le hostname
- Le fichier `predeploy` est **antérieur** au fichier `postdeploy` (preuve de l'ordre d'exécution)

Pour lancer les tests, depuis la racine du repo :

```bash
pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez un `pre_tasks` qui appelle un module `uri:` vers un endpoint inexistant — vérifiez que le `pre_tasks` échoue **avant** que `tasks` ne tournent (preuve de l'ordre `pre_tasks` → `tasks`).
- Ajoutez `meta: flush_handlers` à la fin de `tasks:` et observez le moment exact où le handler tourne — voir le [lab 06](../../06-ecrire-code-handlers/).
- Pour les concepts `serial:`, `strategy:` et `max_fail_percentage:`, passez au [lab 09](../../09-ecrire-code-parallelisme-strategies/).

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/ecrire-code/plays-et-tasks/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
