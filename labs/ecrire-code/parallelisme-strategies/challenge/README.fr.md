# 🎯 Challenge — `serial: 1` + `max_fail_percentage`

## ✅ Objectif

Écrire `challenge/solution.yml` qui pose un fichier marqueur sur **web1.lab et
web2.lab**, dans cet ordre garanti par `serial: 1`.

Vous devez prouver via les **mtimes** que `serial: 1` a bien séquentialisé
l'exécution (web1 traité **complètement** avant que web2 ne commence).

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-parallelisme-strategies
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
```

🔍 **Ce que vous devez voir** dans la sortie :

- Le bandeau `PLAY [...]` apparaît **deux fois** : une fois pour web1, une fois
  pour web2 (parce que `serial: 1` redémarre le play à chaque batch).
- Sur chaque play, vous voyez `Marqueur ...` puis `Pause ...`.
- Le `PLAY RECAP` final montre `changed=1` sur les **deux** hôtes (le marqueur ;
  `pause` ne change rien).
- **Relancez la commande** : le second `PLAY RECAP` doit montrer `changed=0`
  partout. C'est ce que vérifie `test_solution_idempotente`.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/parallelisme-strategies/challenge/tests/
```

Le test vérifie :

- Les 2 fichiers `/tmp/serial-web1.lab.txt` et `/tmp/serial-web2.lab.txt` existent.
- Le **mtime** du fichier sur web1 est **strictement antérieur** à celui de web2
  (preuve mécanique de la séquentialisation).
- Le **second passage** du playbook ne change rien (`changed=0`).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-parallelisme-strategies
```

Supprime les marqueurs sur les 2 webservers pour rejouer le scénario à blanc.

## 💡 Pour aller plus loin

- **`strategy: free`** : ajoutez ce mot-clé au play et observez la différence —
  chaque hôte avance à son propre rythme. À combiner avec `serial:` pour des
  scénarios mixtes.
- **`max_fail_percentage: 30`** : tolère jusqu'à 30 % d'hôtes en échec avant
  d'arrêter. Utile sur des groupes de 20+ hôtes.
- **Lint avec `ansible-lint`** :

   ```bash
   ansible-lint labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
   # Mode strict (production) :
   ansible-lint --profile production \
       labs/ecrire-code/parallelisme-strategies/challenge/solution.yml
   ```
