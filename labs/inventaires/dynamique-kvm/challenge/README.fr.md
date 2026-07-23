# 🎯 Challenge : cibler uniquement les VMs running du lab

Vous avez vu le plugin libvirt en action. Le challenge consiste à **combiner** les groupes dynamiques (`state_running`) et statiques (`lab_vms`) pour cibler **précisément** les VMs du lab qui sont en cours d'exécution.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **`hosts: lab_vms:&state_running`** (intersection : VMs du lab ET running).
2. Pose un fichier marqueur `/tmp/lab57-mark-{{ inventory_hostname }}.txt` qui contient :

   ```text
   VM <nom> running - inventaire dynamique libvirt OK
   ```

   Le `<nom>` est celui du **domaine libvirt** : `web1.lab`, pas `web1`. Le
   marqueur de `web1.lab` s'appelle donc `/tmp/lab57-mark-web1.lab.txt`.

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: "Challenge : cibler les VMs running du lab via plugin libvirt"
  hosts: ???                       # intersection : groupe statique 'lab_vms' ET groupe dynamique 'state_running'
  gather_facts: false
  tasks:
    - name: Poser le marqueur
      ansible.builtin.copy:
        dest: ???                  # /tmp/lab57-mark-<inventory_hostname>.txt
        content: "VM {{ ??? }} {{ ??? }} - inventaire dynamique libvirt OK\n"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Inventaire = dossier**, pas un fichier YAML. Ansible lit tous les `*.yml`
>   de `inventory/`, plus `group_vars/` et `host_vars/`, et fusionne. Lancez
>   avec `-i inventory/` (avec le slash final).
> - **Le nom, c'est celui du domaine libvirt.** `inventory_hostname: name` fait
>   remonter `web1.lab`, ce qu'affiche `virsh list --all`. Un playbook ou un
>   filtre écrit sur `web1` ne matche **rien**, et Ansible ne s'en plaint pas.
> - **Groupes d'état** : `state_running`, `state_shutoff`… Ils viennent des
>   `keyed_groups` de `01-libvirt.yml`, calculés depuis `info.state` que remonte
>   le plugin. Aucun fichier statique ne les déclare.
> - **N'écrivez pas « running » en dur** dans le contenu du marqueur : le
>   marqueur doit **prouver** que vous avez lu l'état remonté par le plugin.
>   La variable est `info.state`.
> - **Pattern `&`** : intersection. `lab_vms:&state_running` = « dans `lab_vms`
>   ET dans `state_running` ». Les deux moitiés comptent : `state_running` seul
>   irait écrire sur toutes les VMs allumées de votre machine, y compris celles
>   qui n'ont rien à voir avec la formation.
> - **Cache du plugin** : si vous éteignez une VM puis relancez le playbook,
>   l'inventaire reflète l'état **au moment du run** (pas de cache par défaut).

Lancez la solution depuis le dossier du lab :

```bash
cd labs/inventaires/dynamique-kvm/
ansible-playbook -i inventory/ challenge/solution.yml
```

Vérifier les marqueurs sur les 4 VMs du lab. La connexion passe par le
`ssh_config` généré par dsoxlab : ni IP, ni utilisateur à connaître.

```bash
SSH_CFG=~/.cache/dsoxlab/ansible-training/ssh_config
for h in control-node.lab web1.lab web2.lab db1.lab; do
  ssh -F "$SSH_CFG" "$h" "cat /tmp/lab57-mark-${h}.txt"
done
```

Sortie attendue (4 lignes) :

```text
VM control-node.lab running - inventaire dynamique libvirt OK
VM web1.lab running - inventaire dynamique libvirt OK
VM web2.lab running - inventaire dynamique libvirt OK
VM db1.lab running - inventaire dynamique libvirt OK
```

## 🧪 Validation

Les tests pytest vérifient que les **4 marqueurs** existent avec le bon contenu,
que le pattern ne résout **que** les 4 VMs du lab (aucune VM étrangère touchée),
et que le playbook est **idempotent**.

```bash
pytest -v challenge/tests/
```

## 🚀 Pour aller plus loin

- Éteignez `web2.lab` (`virsh -c qemu:///system shutdown web2.lab`), relancez le
  playbook : seuls 3 marqueurs sont créés, `web2.lab` n'est plus dans
  `state_running`. Rallumez-le ensuite (`virsh -c qemu:///system start web2.lab`).
- Vérifiez qu'une VM allumée **hors du lab** n'est jamais touchée :
  `ansible -i inventory/ 'lab_vms:&state_running' --list-hosts` doit toujours
  retourner exactement 4 hôtes, quoi qu'il tourne d'autre sur votre machine.
  Comparez avec `ansible -i inventory/ 'all' --list-hosts`.
- Modifiez `01-libvirt.yml` pour ajouter un groupe `production` qui contient
  `web1.lab`, `web2.lab` et `db1.lab` mais **pas** `control-node.lab`. Testez
  avec `ansible -i inventory/ production -m ansible.builtin.ping`.
- Déplacez `ansible_connection: ssh` de `host_vars/` vers `group_vars/lab_vms.yml`
  et relancez : observez Ansible repartir sur `libvirt_qemu` et échouer. C'est la
  précédence, en direct.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
dsoxlab clean inventaires-dynamique-kvm
```

Cette cible supprime ce que la solution a posé sur les managed nodes afin que
vous puissiez relancer la solution from scratch.
