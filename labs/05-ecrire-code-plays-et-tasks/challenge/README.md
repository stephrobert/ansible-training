# 🎯 Challenge — Circuit breaker avec `max_fail_percentage: 0`

Vous avez écrit un play complet avec `pre_tasks` / `tasks` / `post_tasks` / `handlers` / `serial: 1`. Le challenge consiste à ajouter un **circuit breaker** : si une tâche échoue sur un hôte, le play **s'arrête immédiatement** sans propager l'erreur aux autres hôtes du groupe.

C'est exactement ce qu'on attend en production pour ne pas écrire le même bug sur 50 webservers.

## ✅ Objectif

Écrire `solution.yml` à la racine de **ce répertoire**
(`labs/ecrire-code/playbooks/plays-et-tasks/challenge/solution.yml`) qui :

1. Cible **un seul hôte** : `db1.lab` (groupe `dbservers`)
2. Utilise **`pre_tasks` + `tasks` + `post_tasks` + `handlers`** comme dans l'exercice principal
3. Pose un fichier marqueur `/tmp/challenge-predeploy-db1.txt` dans `pre_tasks`
4. Installe `httpd` (Apache) + le démarre + l'active
5. Modifie `/etc/httpd/conf.d/welcome.conf` pour qu'Apache renvoie `Challenge OK from db1.lab` (plutôt que la page par défaut)
6. **Notifie** le handler `Restart httpd` quand `welcome.conf` est modifié
7. Le handler redémarre httpd via `ansible.builtin.systemd state: restarted`
8. Pose un fichier marqueur `/tmp/challenge-postdeploy-db1.txt` dans `post_tasks`
9. Active `serial: 1` et **`max_fail_percentage: 0`** au niveau play

## 🧩 Consignes

1. Créez `challenge/solution.yml` (vide pour démarrer).
2. Indices pour le contenu de `welcome.conf` :

   ```apache
   <Location "/">
     ErrorDocument 200 "Challenge OK from {{ inventory_hostname }}"
   </Location>
   ```

   Plus simple : utilisez `copy:` avec `content:` qui pose `<html><body>Challenge OK from {{ inventory_hostname }}</body></html>` dans `/var/www/html/index.html` après avoir supprimé `welcome.conf`.

3. Lancez la solution depuis la **racine du repo** :

   ```bash
   ansible-playbook labs/ecrire-code/playbooks/plays-et-tasks/challenge/solution.yml
   ```

4. Testez :

   ```bash
   curl http://db1.lab
   ```

   Le `curl` doit retourner exactement :
   `Challenge OK from db1.lab`

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
pytest -v labs/ecrire-code/playbooks/plays-et-tasks/challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajoutez **`strategy: free`** au play et observez la différence dans la sortie console.
- Étendez le challenge à `webservers` (3 hôtes) et activez **`max_fail_percentage: 30`** : si plus de 30 % des hôtes échouent, le play s'arrête.
- Ajoutez un `pre_tasks` qui appelle un module `uri:` vers un endpoint inexistant — vérifiez que le `pre_tasks` échoue **avant** que `tasks` ne tournent (preuve de l'ordre `pre_tasks` → `tasks`).

---

Bonne chance ! 🧠
