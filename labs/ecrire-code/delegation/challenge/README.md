# 🎯 Challenge — `delegate_to` + `run_once`

## ✅ Objectif

Écrire `challenge/solution.yml` qui démontre **deux mécaniques** complémentaires :

1. **Une tâche standard** itère sur tous les `webservers` (web1, web2) et pose
   un marqueur **local** sur chaque hôte : `/tmp/delegation-on-{{ inventory_hostname }}.txt`.
2. **Une tâche déléguée** pose **un seul** fichier sur **db1.lab** (un hôte
   pourtant absent du groupe `webservers`) — preuve que `delegate_to` permet
   d'agir hors-pattern, et que `run_once` empêche le doublon.

## 🧩 Indices

```yaml
---
- name: Challenge - delegation
  hosts: webservers
  become: true
  tasks:
    - name: Marqueur local sur chaque webserver
      ansible.builtin.copy:
        dest: ???        # interpolez inventory_hostname
        content: ???
        mode: "0644"

    - name: Marqueur centralisé sur db1 (déléguer + une seule fois)
      ansible.builtin.copy:
        dest: /tmp/delegation-on-db1.txt
        content: ???
        mode: "0644"
      delegate_to: ???
      run_once: ???
```

À compléter :

- **`delegate_to: db1.lab`** : la tâche s'exécute sur db1, pas sur web1/web2.
- **`run_once: true`** : sans ça, la tâche tournerait 2 fois (une par hôte de
  `webservers`), avec le **même contenu** mais sur le **même** db1.lab → soit
  inutile, soit conflit. `run_once` garantit une seule exécution dans le batch.

> 💡 **Pièges** :
>
> - **`delegate_to:` ne change PAS `inventory_hostname`** : la variable
>   reste celle de l'hôte courant du play. Pour récupérer celle de la
>   cible déléguée, utiliser `delegate_facts: true` + `hostvars[delegate].…`.
> - **`run_once: true` sans `delegate_to`** : la tâche tourne sur **le
>   premier hôte** du batch. Combiné avec `delegate_to: localhost`, c'est
>   le pattern "tâche unique côté control node".
> - **`local_action:`** : raccourci pour `delegate_to: localhost`. Plus
>   lisible quand on n'a qu'**une seule** tâche à exécuter localement.
> - **`become:` sur tâche déléguée** : s'applique à **l'hôte délégué**, pas
>   au play. `become: true` sur une tâche `delegate_to: localhost`
>   demande sudo localement.

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
make -C labs/ecrire-code/delegation clean
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
