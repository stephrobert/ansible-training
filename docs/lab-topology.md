# Topologie du lab Ansible RHCE

## Schéma réseau

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Hôte Linux (KVM / libvirt)                          │
│                                                                      │
│     ┌─────────────────────────────────────────────────────────┐      │
│     │   Réseau libvirt 'lab-ansible' (NAT, 10.10.20.0/24)     │      │
│     │   bridge : virbr-ansible                                │      │
│     │   gateway/DNS : 10.10.20.1                              │      │
│     └─────────────────────────────────────────────────────────┘      │
│              │              │              │              │          │
│   ┌──────────┴───┐  ┌───────┴────┐  ┌──────┴──────┐  ┌────┴──────┐   │
│   │ control-node │  │   web1     │  │   web2      │  │   db1     │   │
│   │ 10.10.20.10  │  │ 10.10.20.21│  │ 10.10.20.22 │  │ 10.10.20.31│  │
│   │ ansible-core │  │ AlmaLinux  │  │ AlmaLinux   │  │ AlmaLinux │   │
│   │ navigator    │  │ 10         │  │ 10          │  │ 10        │   │
│   │ 2 vCPU 2GB   │  │ 1 vCPU 1GB │  │ 1 vCPU 1GB  │  │ 1 vCPU    │   │
│   │              │  │            │  │             │  │ 1.5GB     │   │
│   └──────────────┘  └────────────┘  └─────────────┘  └───────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Groupes Ansible

| Groupe | Hôtes |
|---|---|
| `control` | control-node.lab |
| `webservers` | web1.lab, web2.lab |
| `dbservers` | db1.lab |
| `rhce_lab` | webservers + dbservers (groupe parent) |

## Authentification

- **User Ansible** : `ansible` (membre de `wheel`, sudo NOPASSWD)
- **Clé SSH** : `~/Projets/lab-ansible/ssh/id_ed25519` (regénérée par bootstrap)
- **Root SSH** : désactivé sur tous les hôtes
- **Mot de passe SSH** : désactivé (clé publique uniquement)

## Distribution

**AlmaLinux 10** (cloud generic image) sur les 4 hôtes — équivalent binaire de RHEL 10, cohérent avec le RHCE EX294.

## Cohabitation avec les autres labs sur la même machine

| Lab | Réseau libvirt | Plage IP |
|---|---|---|
| `lab-ansible` (ce lab) | `lab-ansible` (dédié) | 10.10.20.0/24 |
| `kubeadm-kvm` | `default` | 192.168.122.10-21 |
| `kubespray-kvm` | `default` | 192.168.122.50-52 |
| `lab-pulumi` | `default` | DHCP |

Le lab Ansible utilise son propre réseau libvirt, donc **aucun risque de conflit IP** avec les autres labs. Les seuls bonds partagés sont la RAM et le CPU de l'hôte.

## Ressources cumulées

| | RAM | vCPU | Disque |
|---|---|---|---|
| control-node | 2048 MiB | 2 | 20 GiB |
| web1 | 1024 MiB | 1 | 10 GiB |
| web2 | 1024 MiB | 1 | 10 GiB |
| db1 | 1536 MiB | 1 | 15 GiB |
| **Total** | **5632 MiB** (~5.5 GiB) | **5 vCPU** | **55 GiB** (avec backing file ~10 GiB en pratique) |
