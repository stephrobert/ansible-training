# 🎯 Challenge — Play complet sur db1 avec nginx

Vous avez écrit un play complet avec `pre_tasks` / `tasks` / `post_tasks` / `handlers`. Le challenge **reproduit ce pattern** sur un autre hôte (`db1.lab`) pour vérifier que vous maîtrisez l'**anatomie d'un play professionnel**. Le logiciel déployé ne change pas : c'est bien la structure du play qui est le sujet, pas le paquet installé.

> Les concepts de **parallélisme** (`serial:`, `max_fail_percentage:`, `strategy:`) sont l'objet du [lab 09](../../parallelisme-strategies/) — ils ne sont **pas** demandés ici.

## ✅ Objectif

Écrire `solution.yml` à la racine de **ce répertoire**
(`labs/ecrire-code/plays-et-tasks/challenge/solution.yml`) qui :

1. Cible **un seul hôte** : `db1.lab` (groupe `dbservers`)
2. Utilise **`pre_tasks` + `tasks` + `post_tasks` + `handlers`** comme dans l'exercice principal
3. Pose un fichier marqueur `/tmp/challenge-predeploy-db1.txt` dans `pre_tasks`
4. Installe `nginx` + le démarre + l'active
5. Ouvre le service `http` dans **firewalld** (zone publique, `permanent: true` + `immediate: true`) pour rendre la page joignable
6. Pose une page d'accueil qui renvoie `Challenge OK from db1.lab` (plutôt que la page par défaut)
7. **Notifie** le handler `Restart nginx` quand la page est modifiée
8. Le handler redémarre nginx via `ansible.builtin.systemd state: restarted`
8. Pose un fichier marqueur `/tmp/challenge-postdeploy-db1.txt` dans `post_tasks`

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: "Challenge : play complet sur db1 avec nginx"
  hosts: ???
  become: ???
  pre_tasks:
    - name: Marqueur predeploy
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-predeploy-db1.txt
        content: "predeploy {{ inventory_hostname }}\n"   # contenu STABLE
        mode: "0644"

  tasks:
    - name: Installer nginx
      ansible.builtin.dnf:
        name: ???
        state: ???

    - name: Démarrer + activer nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???
        enabled: ???

    - name: Ouvrir le service http dans firewalld
      ansible.posix.firewalld:
        service: ???                       # http
        permanent: ???
        immediate: ???
        state: enabled

    - name: Poser la page d'accueil custom
      ansible.builtin.copy:
        dest: ???                          # /usr/share/nginx/html/index.html
        content: "Challenge OK from {{ ??? }}\n"
        mode: "0644"
      notify: Restart nginx

  post_tasks:
    - name: Marqueur postdeploy (son mtime prouvera l'ordre)
      ansible.builtin.copy:
        dest: ???                          # /tmp/challenge-postdeploy-db1.txt
        content: "postdeploy {{ inventory_hostname }}\n"  # contenu STABLE
        mode: "0644"

  handlers:
    - name: Restart nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: ???                         # restarted
```

> 💡 **Pièges** :
>
> - **Ordre d'exécution** : `pre_tasks` → `tasks` → handlers (notifiés) →
>   `post_tasks`. Si vous mettez le marqueur predeploy dans `tasks:`, le
>   test `mtime predeploy < postdeploy` peut échouer.
> - **Le contenu des marqueurs doit être STABLE** : `predeploy db1.lab`, pas
>   `predeploy db1.lab at 2026-07-17T09:12:33Z`. Ce qui prouve l'ordre, c'est
>   le **mtime** des deux fichiers, que le noyau pose à l'écriture, et que le
>   test compare. Le contenu, lui, ne prouve rien : `ansible_date_time` porte
>   l'heure de la **collecte des facts**, pas celle de l'écriture, et
>   `ansible.cfg` la met en cache 2 heures : les deux marqueurs porteraient
>   donc la MÊME heure et l'horodatage ne prouverait même pas l'ordre qu'on
>   attend de lui.
> - **Un timestamp dans le `content:` casse l'idempotence** : le contenu
>   diffère à chaque run, `copy:` réécrit, et `test_solution_idempotente`
>   exige `changed=0` au second passage. Votre playbook échouerait.
> - **Le test cherche** `Challenge OK from db1.lab` exactement (avec le
>   FQDN). Utilisez `inventory_hostname`, pas `ansible_hostname` (qui est
>   le hostname court).
> - **Le docroot de nginx sur RHEL est `/usr/share/nginx/html`**, pas
>   `/var/www/html` (celui d'Apache). Y écrire `index.html` remplace
>   directement la page par défaut : contrairement à Apache, il n'y a pas de
>   `welcome.conf` à neutraliser au préalable.

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

Le script `tests/test_functional.py` vérifie automatiquement :

- Le fichier `/tmp/challenge-predeploy-db1.txt` existe sur `db1.lab` et contient le hostname
- Le paquet `nginx` est installé
- Le service `nginx` est `running` et `enabled`
- Le port `80` est en `listening`
- Le port `80` est ouvert dans firewalld (zone publique)
- La requête HTTP `http://db1.lab` retourne **200** et contient `Challenge OK from db1.lab`
- Le fichier `/tmp/challenge-postdeploy-db1.txt` existe et contient le hostname
- Le fichier `predeploy` est **antérieur** au fichier `postdeploy` (preuve de l'ordre d'exécution)
- Le **second passage** du playbook ne change rien (`changed=0`)

Pour lancer les tests, depuis la racine du repo :

```bash
pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez un `pre_tasks` qui appelle un module `uri:` vers un endpoint inexistant — vérifiez que le `pre_tasks` échoue **avant** que `tasks` ne tournent (preuve de l'ordre `pre_tasks` → `tasks`).
- Ajoutez `meta: flush_handlers` à la fin de `tasks:` et observez le moment exact où le handler tourne — voir le [lab 06](../../handlers/).
- Pour les concepts `serial:`, `strategy:` et `max_fail_percentage:`, passez au [lab 09](../../parallelisme-strategies/).

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean ecrire-code-plays-et-tasks
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
