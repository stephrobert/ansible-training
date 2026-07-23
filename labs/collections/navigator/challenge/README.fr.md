# 🎯 Challenge — Découvrir, utiliser et valider avec `ansible-navigator`

## ✅ Objectif

Écrire `challenge/solution.yml` (play ciblant `db1.lab`) qui utilise l'**Automation
content navigator** pour toute la boucle et laisse l'état suivant.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Preuve d'exploration | `/tmp/lab-navigator-doc.txt`, `0644`, owner `root`, contient `ansible.posix.sysctl` |
| État kernel | `vm.swappiness = 42`, en live **et** écrit dans `/etc/sysctl.d/70-navigator-lab.conf` |
| Preuve d'inventaire | `/tmp/lab-navigator-inventory.txt`, `0644`, owner `root`, contient `db1.lab` et le groupe `webservers` |
| Idempotence | Un second passage annonce `changed=0` |

`ansible-navigator` tourne sur le **control node** : appelez-le avec
`delegate_to: localhost` et `become: false`. Passez
`--mode stdout --execution-environment false` pour qu'il reste scriptable et ne
tire pas d'image d'EE.

## 🧩 Bloqué ?

```bash
dsoxlab hint collections-navigator
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

Le test pytest+testinfra valide :

- la preuve d'exploration existe (`0644`, root) et cite `ansible.posix.sysctl` ;
- `vm.swappiness` vaut `42` en live sur `db1.lab` et est persisté sous
  `/etc/sysctl.d/` ;
- la preuve d'inventaire résout `db1.lab` et le groupe `webservers` ;
- la solution est **idempotente** (critère RHCE).

## 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
