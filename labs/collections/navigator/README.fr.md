# Lab — Automation content navigator (`ansible-navigator`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les VMs du lab
> doivent répondre au ping Ansible.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → « pong » attendu
> ```
>
> Si KO, lancez `mise install && dsoxlab provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Automation content navigator**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/)

`ansible-navigator` est l'**Automation content navigator** : le front-end moderne
que Red Hat pousse pour remplacer les commandes `ansible-*` éparpillées. Un seul
outil pour `run`, `doc`, `collections`, `inventory`, `config`, `images`, en TUI ou
en `--mode stdout` pour les scripts et la CI. C'est un **objectif d'examen** de la
RHCE EX294 :

- *Use Automation content navigator to find new modules in available Ansible
  Content Collections and use them.*
- *Use Automation content navigator to create inventories and configure the
  Ansible environment.*

Par défaut, `ansible-navigator` exécute tout **dans un Execution Environment** (un
conteneur). Dans ce lab, on passe `--execution-environment false` pour qu'il
utilise l'installation ansible locale : la compétence (les sous-commandes et le
workflow) est identique, sans tirer une image de plusieurs centaines de Mo.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Découvrir** un module dans une collection installée avec
   `ansible-navigator doc <fqcn>` et `ansible-navigator collections`.
2. **Utiliser** ce module découvert dans un playbook pour produire un état système
   réel et vérifiable.
3. **Valider** un inventaire avec `ansible-navigator inventory --list`.

## 🔧 Préparation

```bash
cd $ANSIBLE_TRAINING
ansible-navigator --version
ansible all -m ansible.builtin.ping
```

## 📚 Exercice 1 — Lister collections et modules avec le navigator

```bash
# Parcourir toutes les collections installées
ansible-navigator collections --mode stdout --execution-environment false

# Lire la documentation d'un module sans quitter le navigator
ansible-navigator doc ansible.posix.sysctl --mode stdout --execution-environment false
```

🔍 **Observation** : `ansible-navigator doc <FQCN>` est l'équivalent navigator de
`ansible-doc`. Il montre la doc de la version **installée** et confirme quelle
collection fournit le module (ici `ansible.posix`). C'est exactement la démarche
pour *trouver un nouveau module dans une collection*.

## 📚 Exercice 2 — Utiliser le module découvert

Une fois que vous savez que `ansible.posix.sysctl` existe et ce qu'il attend,
appelez-le depuis un play pour poser un paramètre kernel. L'intérêt du navigator
n'est pas de lire des docs, c'est de passer de *« quel module me faut-il ? »* à
*« le système est dans le bon état »*.

```yaml
- name: Appliquer le module découvert
  ansible.posix.sysctl:
    name: vm.swappiness
    value: "42"
    sysctl_set: true
    state: present
    reload: true
    sysctl_file: /etc/sysctl.d/70-navigator-lab.conf
```

🔍 **Observation** : `sysctl_set: true` change la valeur **live**, `sysctl_file`
la persiste. Le module est idempotent : un second passage n'annonce aucun
changement.

## 📚 Exercice 3 — Valider un inventaire avec le navigator

```bash
ansible-navigator inventory -i mon-inventaire.yml --list \
  --mode stdout --execution-environment false
```

🔍 **Observation** : `ansible-navigator inventory` résout et rend un inventaire
comme `ansible-inventory`. Utilisez-le pour **prouver** qu'un inventaire écrit à la
main se parse, que les groupes et `ansible_host` sont corrects, avant qu'un seul
play ne tourne dessus.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) : utiliser `ansible-navigator`
pour découvrir un module, déposer une **preuve** de cette exploration, utiliser le
module pour poser un état kernel sur `db1.lab`, et valider un inventaire avec
`ansible-navigator inventory`.

## 💡 Pour aller plus loin

- `ansible-navigator run playbook.yml` rejoue un playbook dans un EE et garde un
  **artefact** navigable du run.
- `ansible-navigator config` et `ansible-navigator settings` inspectent la
  configuration Ansible / navigator résolue.
- Un `ansible-navigator.yml` de projet fige l'EE par défaut, la politique de pull
  et le mode pour toute l'équipe.
