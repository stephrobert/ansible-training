# 🎯 Challenge — Cibler avec précision via patterns

Vous avez vu chaque opérateur de pattern individuellement. Le challenge consiste à **combiner** plusieurs opérateurs et à **prouver** que seuls les hôtes attendus reçoivent le marqueur.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **`hosts: all`** (le filtrage se fait via `--limit` au moment de l'exécution).
2. Pose un fichier marqueur `/tmp/lab56-mark-{{ inventory_hostname }}.txt` qui contient `pattern OK on {{ inventory_hostname }}`.

Le test automatique **lance 3 commandes** avec des `--limit` différents et vérifie que **seuls les hôtes attendus** ont reçu le marqueur :

| Run | `--limit` | Hôtes attendus |
|---|---|---|
| 1 | `webservers:&staging` | `web1.lab` uniquement |
| 2 | `webservers:!web1.lab` | `web2.lab` uniquement |
| 3 | `all:!staging` | `web2.lab`, `db1.lab` (pas web1) |

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: Challenge — patterns d'hôtes (le filtrage se fait via --limit)
  hosts: ???                       # 'all' : on cible large, --limit fait le filtre
  become: ???
  gather_facts: false
  tasks:
    - name: Poser le marqueur
      ansible.builtin.copy:
        dest: ???                  # /tmp/lab56-mark-<inventory_hostname>.txt
        content: "pattern OK on {{ ??? }}\n"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`hosts: all` + `--limit`** vs **`hosts: <pattern>`** : préférer
>   `hosts: all` dans le playbook et **passer le filtre au runtime** via
>   `--limit`. Sinon, on doit éditer le YAML pour chaque cible —
>   anti-pattern.
> - **Les opérateurs** : `:` = union, `&` = intersection, `!` = exclusion,
>   `*` = wildcard. Les combiner avec attention :
>   `webservers:&staging` = "dans webservers ET dans staging".
> - **L'inventaire du lab** définit un groupe `staging` qui contient
>   uniquement `web1.lab`. Vérifiez avec `ansible-inventory -i ... --graph`
>   avant de lancer le playbook.
> - **`changed_when` non nécessaire** : `copy:` est nativement idempotent
>   sur le contenu.

Lancez la première démo manuellement pour valider :

```bash
cd labs/inventaires/patterns-hotes/
ansible-playbook -i inventory/hosts.yml challenge/solution.yml \
    --limit 'webservers:&staging'
ssh ansible@web1.lab cat /tmp/lab56-mark-web1.lab.txt
```

Le test pytest applique automatiquement les 3 patterns successivement.

## 🧪 Validation

```bash
pytest -v challenge/tests/
```

## 🚀 Pour aller plus loin

- Ajouter un 4e cas de test : `--limit '*1.lab'` (devrait toucher `web1.lab` ET `db1.lab`).
- Modifier l'inventaire pour ajouter un groupe `dev` contenant `web1.lab` et `db1.lab`. Tester `dev:!monitoring` (= web1, car db1 est dans monitoring).
- Comparer les sorties de `--list-hosts` et `--limit` : la première fait un dry-run de la résolution, la seconde l'applique.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/inventaires/patterns-hotes/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
