# Durcir la config de l'application sans toucher aux voisins

## La situation

L'application de **db1.lab** lit `/etc/myapp.conf`, et trois changements
tombent en même temps : l'API déménage sur un nouveau domaine derrière TLS,
le port de service passe à 8443, et SSL doit être activé. Le piège est écrit
dans le fichier lui-même : il empile une section `[server]` et une section
`[client]`, et toutes deux déclarent `ssl_enabled=false`. Seul le côté
serveur doit basculer à `true` : une substitution aveugle basculerait aussi
le client et casserait sa négociation. Vous intervenez depuis
**control-node.lab**, sur un fichier qui doit ressortir modifié au scalpel.

Votre mission :

1. Faire passer l'URL de l'API en **https sur son nouveau domaine**, partout
   où elle apparaît, en gardant le chemin intact.
2. Monter le **port à 8443** en préservant le préfixe `port=`, plutôt que de
   réécrire toute la ligne.
3. Activer SSL **dans la seule section `[server]`**, en **bornant la zone de
   substitution** plutôt qu'en faisant confiance au motif.
4. Prouver que les dégâts collatéraux sont nuls : `[client]` affiche toujours
   `ssl_enabled=false`, et un second passage ne change rien.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/

## Challenge `replace:`

### Énoncé

Le setup du lab a posé sur **db1.lab** le fichier `/etc/myapp.conf` suivant :

```ini
url=http://api-old.example.com/v1
port=8080
[server]
ssl_enabled=false
host=localhost
[client]
ssl_enabled=false
host=localhost
```

Écrivez `solution.yml` qui transforme ce fichier pour obtenir exactement
cet état :

```ini
url=https://api.example.com/v1
port=8443
[server]
ssl_enabled = true
host=localhost
[client]
ssl_enabled=false
host=localhost
```

Autrement dit :

1. L'URL de l'API passe en **https** sur le nouveau domaine
   `api.example.com` (le chemin `/v1` est préservé).
2. Le port passe de 8080 à **8443**, en conservant le préfixe `port=`.
3. `ssl_enabled` passe à `true` (avec espaces : `ssl_enabled = true`)
   **uniquement dans la section `[server]`** : la section `[client]`
   garde `ssl_enabled=false` à l'identique.
4. Un 2e run du playbook ne change rien (idempotent).

### Critères de réussite

- `grep https://api.example.com /etc/myapp.conf` matche, et
  `api-old.example.com` a disparu.
- `grep port=8443 /etc/myapp.conf` matche, et `port=8080` a disparu.
- Entre `[server]` et `[client]` : `ssl_enabled = true`.
- Après `[client]` : toujours `ssl_enabled=false`.
- 1er run : `changed`. 2e run : `ok` (idempotent).

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-fichiers-replace
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.
