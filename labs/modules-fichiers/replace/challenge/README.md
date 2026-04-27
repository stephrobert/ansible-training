# Challenge `replace:`

## Énoncé

Sur **db1.lab**, écrivez `solution.yml` qui :

1. Crée un fichier `/etc/myapp/multi.conf` avec 3 sections `[db]`, `[cache]`, `[api]`,
   chacune contenant `host=localhost` et `port=NNNN`.
2. Modifie **uniquement le `host` de la section `[api]`** pour qu'il devienne
   `host=api.example.com`.
3. Vérifie que les sections `[db]` et `[cache]` ont gardé `host=localhost`.

## Critères de réussite

- 1er run : `changed`.
- 2e run : `ok` (idempotent).
- `grep -A 2 '\[api\]' /etc/myapp/multi.conf` montre `host=api.example.com`.
- Les autres sections sont **inchangées**.

## Indices

- `before:` et `after:` permettent de limiter la zone de substitution.
- La fin de section est marquée par `^\[` (début de section suivante) ou par EOF.
