# Un seul outil pour trouver le module, l'utiliser et vérifier l'inventaire

## La situation

Votre équipe standardise sur l'**Automation content navigator**. L'ancien réflexe,
c'était `ansible-doc` ici, `ansible-inventory` là, `ansible-playbook` pour finir :
trois commandes, trois comportements, rien qui corresponde à ce que la production
exécute réellement (des Execution Environments). L'examen RHCE attend désormais que
vous dégainiez `ansible-navigator` pour toute la boucle.

Un collègue a besoin de poser un paramètre kernel sur **db1.lab** mais ne se
souvient plus quel module le fait, ni quelle collection le fournit. Plutôt que de
deviner, vous allez *trouver* le module avec le navigator, puis l'*utiliser*, puis
*valider* l'inventaire que le play va cibler, le tout avec le même outil.

Votre mission, depuis **control-node.lab** :

1. Utiliser `ansible-navigator doc` pour trouver le module qui gère les entrées
   `sysctl`, confirmer la collection dont il vient, et garder une **preuve** de
   cette exploration sur `db1.lab` (le nom pleinement qualifié du module doit y
   figurer).
2. Utiliser ce module découvert pour poser `vm.swappiness = 42` sur `db1.lab`, en
   live et persistant, de façon idempotente.
3. Écrire un petit inventaire et le valider avec `ansible-navigator inventory
   --list`, puis garder la sortie résolue comme preuve sur `db1.lab`.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/

## 🎯 Challenge — Découvrir, utiliser et valider avec `ansible-navigator`

### ✅ Objectif

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

### 🧩 Bloqué ?

```bash
dsoxlab hint collections-navigator
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

### 🧪 Validation automatisée

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

Le test pytest+testinfra valide :

- la preuve d'exploration existe (`0644`, root) et cite `ansible.posix.sysctl` ;
- `vm.swappiness` vaut `42` en live sur `db1.lab` et est persisté sous
  `/etc/sysctl.d/` ;
- la preuve d'inventaire résout `db1.lab` et le groupe `webservers` ;
- la solution est **idempotente** (critère RHCE).

### 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
