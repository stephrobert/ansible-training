# Context — Stop maintaining an inventory the hypervisor already knows

The static inventory lies. Two VMs listed in it were destroyed last month, a
third was renamed, and every run wastes time timing out on hosts that no longer
exist. Meanwhile libvirt knows exactly what is running, right now, on the
hypervisor. Worse, the file lists shut-down VMs alongside live ones, so a play
aimed at "everything" always fails on the ones that are off. You wire the
inventory to the source of truth from **control-node.lab**.

Your mission:

1. Have libvirt **discover the VMs automatically** through the inventory plugin,
   remembering that the inventory becomes a **directory** the plugin composes,
   not a single hand-written file.
2. Use the **dynamic state groups** the plugin generates, which no static file
   declares, to tell running VMs from the rest.
3. Target the **intersection** of the lab's static group and the running VMs: a
   VM that is off must not be attempted, and a running VM outside the lab must
   not be touched.
4. Drop a marker on each VM actually reached, proving the discovery reflects the
   state **at run time**.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/dynamiques/plugin-libvirt-kvm/
