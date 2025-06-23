# 🎯 Challenge - Inventaire dynamique avec filtrage des conteneurs actifs

Dans ce challenge, vous allez mettre en pratique l’utilisation des **inventaires
dynamiques** en filtrant automatiquement les conteneurs Incus **actifs
uniquement**. Vous apprendrez également à **organiser dynamiquement les hôtes
par groupe** à l’aide du plugin fourni par la collection `kmpm.incus`.

## ✅ Objectif

* Configurer un inventaire dynamique pour les conteneurs Incus
* Filtrer les conteneurs actifs

## 🧹 Consignes

Commencez par stopper le conteneur `web01` si ce n’est pas déjà fait :

```bash
incus stop web01
```

1. Modifiez le fichier `incus.yml` dans le dossier
   `05-Inventaires-Dynamiques`
2. Configurez-le pour filtrer les conteneurs à l'état `running`
3. Relancez la commande d'inventaire pour vérifier que seuls les conteneurs
   actifs sont listés :

```bash
ansible-inventory --graph
```

## 👍 Critères de réussite

Le test `test_inventory.py` vérifiera que :

* L’inventaire ne contient **aucun** hôte arrêté

## 🔍 Validation

Lancez le test avec la commande suivante :

```bash
pytest -v
```

Le test doit passer sans erreur, comme ceci :

```bash
=== test session starts ===
platform linux -- Python 3.12.3, pytest-8.4.0, pluggy-1.6.0 -- /home/outscale/.local/share/pipx/venvs/pytest/bin/python
cachedir: .pytest_cache
rootdir: /home/outscale/Projets/perso/ansible-training/05-Inventaires-Dynamiques
plugins: testinfra-10.2.2
collected 1 item

challenge/tests/test_inventory.py::test_web01_not_in_inventory PASSED                                                                                                                                                                                                     [100%]

==== 1 passed in 0.31s ====
```

---

Bonne exploration ! Et souvenez-vous : **le filtrage dynamique évite bien des
erreurs** 🤖
