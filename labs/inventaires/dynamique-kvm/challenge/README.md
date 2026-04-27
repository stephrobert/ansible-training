# 🎯 Challenge — Cibler uniquement les VMs running du lab

Vous avez vu le plugin libvirt en action. Le challenge consiste à **combiner** les groupes dynamiques (`state_running`) et statiques (`lab_vms`) pour cibler **précisément** les VMs du lab qui sont en cours d'exécution.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible **`hosts: lab_vms:&state_running`** (intersection : VMs du lab ET running).
2. Pose un fichier marqueur `/tmp/lab57-mark-{{ inventory_hostname }}.txt` qui contient :

   ```text
   VM <nom> running - inventaire dynamique libvirt OK
   ```

## 🧩 Consignes

Squelette à compléter :

```yaml
---
- name: Challenge — cibler les VMs running du lab via plugin libvirt
  hosts: ???                       # intersection : groupe statique 'lab_vms' ET groupe dynamique 'state_running'
  become: ???
  gather_facts: false
  tasks:
    - name: Poser le marqueur
      ansible.builtin.copy:
        dest: ???                  # /tmp/lab57-mark-<inventory_hostname>.txt
        content: "VM {{ ??? }} running - inventaire dynamique libvirt OK\n"
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Inventaire = dossier**, pas un fichier YAML. Le plugin libvirt scanne
>   tous les `*.yml` dans `inventory/` et compose les groupes. Lancez avec
>   `-i inventory/` (avec le slash final).
> - **Groupes dynamiques libvirt** : `state_running`, `state_shutoff`,
>   `state_paused`. Ils sont **générés par le plugin**, pas définis dans
>   votre inventaire statique.
> - **Pattern `&`** : intersection. `lab_vms:&state_running` = "dans
>   `lab_vms` ET dans `state_running`". Permet de combiner statique et
>   dynamique.
> - **Cache du plugin** : si vous shutdown une VM puis relancez le
>   playbook, l'inventaire dynamique reflète l'état **au moment du run**
>   (pas de cache par défaut).

Lancez la solution depuis le dossier du lab :

```bash
cd labs/inventaires/dynamique-kvm/
ansible-playbook -i inventory/ challenge/solution.yml
```

Vérifier les marqueurs sur les 4 VMs du lab :

   ```bash
   for h in control-node web1 web2 db1; do
     ssh ansible@$h.lab "cat /tmp/lab57-mark-${h}.txt"
   done
   ```

   Sortie attendue (4 lignes) :

   ```text
   VM control-node running - inventaire dynamique libvirt OK
   VM web1 running - inventaire dynamique libvirt OK
   VM web2 running - inventaire dynamique libvirt OK
   VM db1 running - inventaire dynamique libvirt OK
   ```

## 🧪 Validation

Le test pytest vérifie que les **4 fichiers marqueurs** existent sur les VMs running du lab.

```bash
pytest -v challenge/tests/
```

## 🚀 Pour aller plus loin

- Arrêtez `web2` (`virsh shutdown web2`), relancez le playbook : seuls 3 marqueurs sont créés (web2 n'est plus dans `state_running`).
- Démarrez une VM extérieure au lab (`virsh start nixos-lab` par exemple) et vérifiez que le pattern `lab_vms:&state_running` ne la touche **pas** (filtre `lab_vms` exclu).
- Modifiez `01-libvirt.yml` pour ajouter un groupe `production` qui contient `web1`, `web2`, `db1` mais **pas** `control-node`. Tester `ansible production -m ping`.

---

Bonne chance ! 🧠

## 🧹 Reset

Pour rejouer le challenge dans un état neutre :

```bash
make -C labs/inventaires/dynamique-kvm/ clean
```

Cette cible désinstalle/supprime ce que la solution a posé sur les managed
nodes (paquets, fichiers, services, règles firewall) afin que vous puissiez
relancer la solution from scratch.
