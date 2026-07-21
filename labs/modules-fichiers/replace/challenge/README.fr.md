# Challenge `replace:`

## Énoncé

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

## Critères de réussite

- `grep https://api.example.com /etc/myapp.conf` matche, et
  `api-old.example.com` a disparu.
- `grep port=8443 /etc/myapp.conf` matche, et `port=8080` a disparu.
- Entre `[server]` et `[client]` : `ssl_enabled = true`.
- Après `[client]` : toujours `ssl_enabled=false`.
- 1er run : `changed`. 2e run : `ok` (idempotent).

## Indices

- `before:` et `after:` bornent la zone de substitution : c'est ce qui
  protège la section `[client]`.
- Attention : combiné à `before:`/`after:`, l'ancrage `^` ne se comporte
  pas comme en mode MULTILINE, retirez-le dans la zone bornée.
- Pour changer le port sans réécrire toute la ligne, un groupe de capture
  (`\g<1>`) préserve le préfixe.
- Si votre regexp matche encore le texte de remplacement, l'idempotence
  est cassée : le 2e run reste `changed`.
