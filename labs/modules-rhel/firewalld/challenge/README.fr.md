# Ouvrir la stack web sans laisser la porte ouverte au reboot

## La situation

L'application passe en production sur **web1.lab** ce soir : le site public en
HTTP et HTTPS, plus deux ports dont l'équipe de dev a encore besoin pour son
instance de staging. La mise en service précédente explique très bien pourquoi
plus personne ne fait confiance aux commandes de pare-feu tapées à la main. Les
règles avaient été appliquées à la console, avaient fonctionné tout l'après-midi,
et avaient disparu au reboot de maintenance : le site était injoignable à 6 h et
personne ne comprenait pourquoi. Vous refaites tout depuis **control-node.lab**.

Votre mission :

1. Vous assurer que firewalld est **installé, démarré et activé au boot** sur
   **web1.lab**, avant d'écrire la moindre règle dans le vide.
2. Autoriser les deux **services web prédéfinis** dans la zone publique, par
   leur nom de service plutôt que par des numéros de ports bruts.
3. Ouvrir les deux **ports custom du staging** dans la même zone.
4. Chaque règle doit être **active tout de suite et survivre au reboot** :
   n'obtenir que l'un des deux, c'est exactement le piège qui a fait tomber le
   site.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-firewalld/

## 🎯 Challenge — Firewalld pour une web stack

### ✅ Objectif

Sur **web1.lab**, configurer **firewalld** pour exposer une stack web :

- **2 services prédéfinis** : `http` (80), `https` (443)
- **2 ports custom** : `8080/tcp` (app dev), `8443/tcp` (app dev TLS)

Toutes les règles doivent être **persistantes** (`permanent: true`) **ET**
**actives immédiatement** (`immediate: true`).

### 🧩 Pourquoi `permanent` ET `immediate` ?

| Combinaison | Effet |
| --- | --- |
| `permanent: true` seul | La règle est écrite dans la config persistente, **mais pas active**. Il faut un `firewall-cmd --reload` pour qu'elle s'applique. |
| `immediate: true` seul | La règle est active maintenant, **mais perdue au reboot**. |
| **Les deux** | Active maintenant **et** persistante — c'est ce qu'on veut quasi toujours. |

### 🧩 Squelette

```yaml
---
- name: Challenge - firewalld web stack
  hosts: web1.lab
  become: true

  tasks:
    - name: Installer firewalld
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: Démarrer et activer firewalld
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Autoriser http + https (services prédéfinis)
      ansible.posix.firewalld:
        service: ???
        state: enabled
        permanent: ???
        immediate: ???
        zone: public
      loop: ???

    - name: Ouvrir les ports custom 8080/tcp + 8443/tcp
      ansible.posix.firewalld:
        port: ???
        state: enabled
        permanent: ???
        immediate: ???
        zone: public
      loop:
        - 8080/tcp
        - 8443/tcp
```

> 💡 **Pièges** :
>
> - **`permanent: true` + `immediate: true`** ensemble : règle
>   persistante au reboot ET active maintenant. **Toujours** les deux pour
>   un lab/prod normal.
> - **`permanent` seul** : modifie uniquement la config persistante,
>   pas la table runtime. Il faut un `firewall-cmd --reload` après.
> - **`zone:`** : sans, utilise la zone par défaut (`public` sur AlmaLinux).
>   Pour cloisonner, utiliser `internal`, `dmz`, `trusted` selon la
>   topologie.
> - **`service:` vs `port:`** : préférer `service: http` (plus lisible,
>   portable) plutôt que `port: 80/tcp`. Le service est défini dans
>   `/usr/lib/firewalld/services/`.

### 🚀 Lancement

```bash
ansible-playbook labs/modules-rhel/firewalld/challenge/solution.yml
ansible web1.lab -b -m ansible.builtin.command -a "firewall-cmd --list-all"
```

🔍 **Vérifications manuelles** :

```bash
# Runtime (--query-service)
ansible web1.lab -b -m ansible.builtin.shell -a "firewall-cmd --query-service=http && firewall-cmd --query-service=https"
# Permanent
ansible web1.lab -b -m ansible.builtin.shell -a "firewall-cmd --permanent --query-port=8080/tcp && firewall-cmd --permanent --query-port=8443/tcp"
```

### 🧪 Validation automatisée

> ⏱️ **Un test redémarre db1** (environ 90 s). Il est marqué `slow`, et il est
> là volontairement : la persistance après redémarrage est le piège qui fait
> échouer les candidats RHCSA et RHCE, et lire le fichier de configuration
> n'en prouve rien. Le temps de vos essais, vous pouvez l'écarter :
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/firewalld/challenge/tests/
> ```
>
> Lancez la suite complète au moins une fois avant de considérer le
> challenge terminé.

```bash
pytest -v labs/modules-rhel/firewalld/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-rhel-firewalld
```

### 💡 Pour aller plus loin

- **Création d'une zone custom** : `zone: dmz` accepte une zone existante
  mais ne la crée pas. Pour en créer, utilisez `community.general.firewalld_info`
  ou un fichier `/etc/firewalld/zones/<zone>.xml` via `template:`.
- **Rich rules** : `rich_rule:` permet de filtrer par IP source, faire des
  rate-limits, etc.
- **`source:`** : autoriser un sous-réseau au lieu d'un service
  (`source: 10.10.20.0/24`).
- **Lint** :

   ```bash
   ansible-lint labs/modules-rhel/firewalld/challenge/solution.yml
   ```
