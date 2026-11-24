# Nginx annonce son numéro de version à toute la planète

## La situation

Le rapport de pentest est revenu avec deux remarques qui ne coûtent rien à
corriger et qui traînent depuis un an : **db1.lab** répond à chaque requête
HTTP avec sa version exacte de nginx dans l'en-tête `Server`, et signe ses
pages d'erreur des mêmes détails. De la reconnaissance offerte à qui scanne la
plage. Second point du rapport : les réponses ne portent aucun en-tête
`X-Content-Type-Options`, et laissent donc les navigateurs deviner eux-mêmes le
type des contenus servis. Changer la configuration, c'est deux lignes. La faire
prendre effet **sans redémarrer nginx à chaque passage du playbook**, et
laisser une trace pour l'audit, voilà le vrai travail. Vous opérez depuis
**control-node.lab**.

Votre mission :

1. Sur `db1.lab`, durcir la configuration de `nginx` pour qu'il cesse
   d'annoncer sa version, puis lui faire refuser le MIME sniffing.
2. Faire **notifier deux handlers** par la tâche de durcissement : le
   rechargement, et une entrée horodatée dans un journal local que les
   auditeurs pourront lire.
3. Préférer un **reload** à un restart, et forcer les handlers à tourner dans
   le même play pour vérifier l'effet immédiatement.
4. Le prouver de l'extérieur : l'en-tête `Server` doit valoir exactement
   `nginx`, sans version, la réponse doit porter `X-Content-Type-Options:
   nosniff`, et un second passage ne doit notifier personne.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/

## 🎯 Challenge — Deux handlers, une tâche, et flush_handlers

Vous avez écrit une tâche qui notifie un handler. Le challenge consiste à
déclencher **deux handlers depuis une seule tâche** et à forcer leur exécution
**immédiate** via `meta: flush_handlers` pour tester la nouvelle config dans
le même play.

### ✅ Objectif

Écrire `solution.yml` qui :

1. Cible `db1.lab`
2. Installe `nginx`, le démarre, l'active
3. Modifie `/etc/nginx/nginx.conf` pour poser **`server_tokens off;`** ET
   **`add_header X-Content-Type-Options "nosniff";`** dans le bloc `http`, via
   **deux tâches `lineinfile`**

   > **Note pédagogique** : `server_tokens off;` fait à lui seul ce qu'Apache
   > demandait en deux directives (`ServerTokens Prod` + `ServerSignature
   > Off`) : il retire la version de l'en-tête `Server` **et** de la signature
   > des pages d'erreur. Le second durcissement est donc un autre point du
   > rapport de pentest, l'en-tête `nosniff`.
   >
   > Ici, contrairement à `httpd.conf`, la directive `validate: nginx -t -c %s`
   > **fonctionne** : `nginx.conf` est autonome (ses `include` sont en chemins
   > absolus), donc nginx sait valider le fichier temporaire que lui passe
   > `%s`. Utilisez-la sur les deux tâches.
4. La **première tâche** (`server_tokens`) notifie **deux handlers** :
   `Reload nginx` ET `Notifier journal local` (un fichier journal)
5. La **deuxième tâche** (`add_header`) notifie uniquement `Reload nginx`
6. Après les deux modifications, force le déclenchement des handlers via
   **`meta: flush_handlers`**
7. **Teste** l'effet via `uri:` qui appelle `http://localhost` et capture
   le header `Server`

Squelette des handlers :

```yaml
handlers:
  - name: Reload nginx
    ansible.builtin.systemd:
      name: ???
      state: ???              # reloaded ≠ restarted, choisir le moins disruptif

  - name: Notifier journal local
    ansible.builtin.lineinfile:
      path: /var/log/ansible-handlers.log
      line: "Config nginx modifiée le {{ ??? }}"   # fact magique : timestamp ISO 8601
      create: ???
      mode: "0644"
```

> 💡 **Pièges** :
>
> - `state: reloaded` recharge la config sans tuer les connexions actives
>   (préférable à `restarted` pour nginx).
> - Les deux directives vont dans le bloc `http { ... }` : pensez à
>   `insertafter:` pour ne pas les écrire en dehors, où nginx les refuserait.
> - Le fact magique du timestamp est dans `ansible_date_time`, chercher la
>   sous-clé qui donne le format ISO 8601.
> - `create: true` est nécessaire pour le **premier** run (le fichier journal
>   n'existe pas encore).

### 🧩 Consignes

1. Créez `challenge/solution.yml`.
2. Lancez :

   ```bash
   ansible-playbook labs/ecrire-code/handlers/challenge/solution.yml
   ```

3. Au **premier run**, vous voyez les **deux handlers** tourner (notifiés par
   les deux tâches).
4. Au **second run**, **aucun handler** ne tourne (`changed=0`).

### 🧪 Validation

Le script `tests/test_functional.py` vérifie automatiquement sur **db1.lab** :

- `nginx` est installé, running, enabled
- `/etc/nginx/nginx.conf` contient `server_tokens off;`
- `/etc/nginx/nginx.conf` contient un `add_header X-Content-Type-Options`
- Le fichier journal `/var/log/ansible-handlers.log` existe et contient une
  entrée, preuve que le **second handler** s'est bien déclenché
- La requête HTTP sur `db1.lab` retourne **200**
- Le **header Server** dans la réponse HTTP est exactement **`nginx`**
  (sans version), preuve que `server_tokens off;` est appliqué (le handler
  reload a bien tourné)
- La réponse porte **`X-Content-Type-Options: nosniff`**, même preuve pour la
  seconde tâche : la directive dans le fichier ne suffit pas, il faut que le
  reload ait eu lieu

```bash
pytest -v labs/ecrire-code/handlers/challenge/tests/
```

### 🚀 Pour aller plus loin

- Refaites le challenge en utilisant **`listen:`** sur un topic
  `nginx-config-changed`. Les deux tâches notifient ce topic, et les deux
  handlers l'écoutent. Sortie identique, code plus découplé.
- Provoquez volontairement une **erreur de syntaxe** dans `nginx.conf`
  (par exemple `server_tokens Garbage;`). Le `validate:` doit empêcher
  l'écriture du fichier ET le handler ne doit **pas** être notifié. Sur nginx
  cet exercice marche vraiment, alors qu'il était impossible sur `httpd.conf`.

---

Bonne chance ! 🧠

### 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean ecrire-code-handlers
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
