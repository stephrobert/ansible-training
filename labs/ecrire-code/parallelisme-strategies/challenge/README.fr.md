# 🎯 Challenge — `serial: 1` + `max_fail_percentage`

## ✅ Objectif

Écrire `challenge/solution.yml` qui pose un fichier marqueur sur **web1.lab et
web2.lab**, dans cet ordre garanti par `serial: 1`.

Vous devez prouver via les **mtimes** que `serial: 1` a bien séquentialisé
l'exécution (web1 traité **complètement** avant que web2 ne commence).

## 🧩 Indices

- Cible : groupe `webservers` (donc 2 hôtes web1 + web2).
- Au niveau du **play**, activez deux mots-clés :
  - `serial: 1` → un hôte à la fois
  - `max_fail_percentage: 0` → arrêt immédiat à la première erreur
- Une tâche `ansible.builtin.copy` qui pose `/tmp/serial-{{ inventory_hostname }}.txt`.
  Le contenu doit être **stable** (par exemple `vague {{ inventory_hostname }}`) :
  c'est le **mtime** du fichier qui prouve la séquentialisation, jamais son contenu.
- Une seconde tâche `ansible.builtin.pause` de 2 secondes pour que le **mtime**
  de web1 soit strictement antérieur à celui de web2.

Squelette à compléter :

```yaml
---
- name: Challenge - serial 1 sur 2 webservers
  hosts: ???
  become: true
  serial: ???
  max_fail_percentage: ???

  tasks:
    - name: Marqueur de vague
      ansible.builtin.copy:
        dest: ???
        content: ???                   # contenu STABLE, cf. le piège ci-dessous
        mode: "0644"

    - name: Pause pour que les mtimes soient distincts
      ansible.builtin.pause:
        seconds: ???
```

> 💡 **Pièges** :
>
> - **`serial: 1`** = rolling 1-par-1 (lent, mais sûr). Sur 2 webservers,
>   le test `mtime web1 < web2` ne passe que si web1 est traité **avant**
>   web2 — pas garanti par défaut. La pause aide à séparer les mtimes.
> - **Le contenu du marqueur doit être STABLE.** La tentation est d'y écrire
>   `{{ ansible_date_time.iso8601 }}` « pour horodater ». Deux raisons de ne
>   pas le faire, et la seconde est fatale :
>
>   1. Ça ne prouve rien de plus. Ce fact porte l'heure de la **collecte des
>      facts**, pas celle de l'écriture du fichier. Le `mtime`, lui, est posé
>      par le noyau au moment exact de l'écriture : c'est le seul témoin de la
>      vague. Pire, `ansible.cfg` met les facts en cache pendant 2 heures : le
>      même horodatage serait recopié sur les deux hôtes.
>   2. Le contenu changerait à chaque run, `copy:` rendrait **toujours
>      `changed`**, et `test_solution_idempotente` exige `changed=0` au second
>      passage. Votre playbook échouerait.
> - **`strategy: linear`** (défaut) = play-bloquant : tous les hôtes
>   doivent finir une tâche avant de passer à la suivante. **`free`** =
>   chaque hôte avance à son rythme — rare en prod, utile en démo.
> - **`max_fail_percentage`** : tolérance au-delà de laquelle le play
>   s'arrête. Different de `any_errors_fatal` qui est tolérance zéro.
> - **`forks`** dans `ansible.cfg` (défaut 5) limite le parallélisme global.
>   Avec `serial: 10` mais `forks: 5`, vous traitez 5-par-5.

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
