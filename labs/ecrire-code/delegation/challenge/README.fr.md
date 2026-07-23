# 🎯 Challenge — `delegate_to` + `run_once`

## ✅ Objectif

Écrire `challenge/solution.yml` qui démontre **deux mécaniques** complémentaires :

1. **Une tâche standard** itère sur tous les `webservers` (web1, web2) et pose
   un marqueur **local** sur chaque hôte : `/tmp/delegation-on-{{ inventory_hostname }}.txt`.
2. **Une tâche déléguée** pose **un seul** fichier sur **db1.lab** (un hôte
   pourtant absent du groupe `webservers`) — preuve que `delegate_to` permet
   d'agir hors-pattern, et que `run_once` empêche le doublon.

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-delegation
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/delegation/challenge/solution.yml
```

🔍 **Ce que vous devez voir** :

- 1ère tâche : `changed: [web1.lab]` et `changed: [web2.lab]` (deux exécutions).
- 2ème tâche : **une seule** ligne `changed: [web1.lab -> db1.lab]` (notation
  délégation : *ce qu'on cible* → *où on agit*). Le `-> db1.lab` est crucial.

Vérifiez :

```bash
# Sur les webservers (marqueurs locaux)
ansible webservers -m ansible.builtin.command \
    -a "ls /tmp/delegation-on-*.txt"

# Sur db1 (marqueur délégué)
ansible db1.lab -m ansible.builtin.command \
    -a "ls /tmp/delegation-on-db1.txt"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/delegation/challenge/tests/
```

Le test vérifie :

- `/tmp/delegation-on-web1.lab.txt` sur **web1**.
- `/tmp/delegation-on-web2.lab.txt` sur **web2**.
- `/tmp/delegation-on-db1.txt` sur **db1** (preuve `delegate_to`).
- **Aucun** `/tmp/delegation-on-db1.txt` sur web1 ni web2 (preuve isolation).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-delegation
```

## 💡 Pour aller plus loin

- **`delegate_facts: true`** : les facts collectés sur l'hôte délégué sont
  enregistrés sur l'hôte cible (utile pour partager une info de db1 vers les
  webservers).
- **`local_action`** = `delegate_to: localhost`. Forme historique encore vue.
- **Pattern load-balancer** : avant de redémarrer un webserver, déléguer à
  l'hôte du LB pour le drainer. Après le restart, déléguer à nouveau pour le
  ré-injecter. Combiné avec `serial: 1` (lab 09), c'est le rolling deploy
  classique.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/delegation/challenge/solution.yml
   ```
