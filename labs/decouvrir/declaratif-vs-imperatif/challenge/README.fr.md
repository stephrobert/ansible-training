# 🎯 Challenge : convertir le script Bash impératif en playbook idempotent

## ✅ Objectif

Le fichier `scripts/install-nginx-impératif.sh` déploie nginx de façon
**impérative** : il enchaîne des commandes et, pire, **ajoute** une ligne à la
page d'accueil à chaque exécution, donc il **dérive**. Votre mission est le
grand classique de l'EX294 : **le réécrire en un playbook Ansible déclaratif**
qui produit le **même état système** sur `web1.lab`, mais qui **converge** au
lieu de dériver.

Écrivez votre playbook dans `challenge/solution.yml`. Il doit atteindre
exactement cet état, et l'atteindre de façon **idempotente** (`changed=0` au
second passage).

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `web1.lab` |
| Paquet | `nginx` installé (`state: present`) |
| Service | `nginx` démarré **et** activé au boot |
| Pare-feu | service `http` ouvert, **permanent et immédiat** |
| Page d'accueil | `/usr/share/nginx/html/index.html` contient **exactement une** ligne `<p>Servi par ...</p>` |
| Idempotence | 2e passage du playbook : `changed=0` dans le `PLAY RECAP` |

## 🧩 Squelette : `challenge/solution.yml`

```yaml
---
- name: Déployer nginx de façon déclarative (équivalent idempotent du script Bash)
  hosts: ???                      # le nœud qui sert réellement la page
  become: ???

  tasks:
    - name: Installer le paquet nginx
      ansible.builtin.dnf:
        name: ???
        state: ???                # present, pas latest (voir les pièges)

    - name: Ouvrir le service http dans firewalld
      ansible.posix.firewalld:
        service: ???
        permanent: ???            # survit à un reload ou à un reboot
        immediate: ???            # prend effet tout de suite, sans reload
        state: enabled

    - name: Démarrer nginx et l'activer au boot
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Garantir une UNIQUE ligne « Servi par ... » dans index.html
      ansible.builtin.lineinfile:
        path: /usr/share/nginx/html/index.html
        regexp: ???               # le motif qui identifie la ligne
        line: ???                 # ex : "<p>Servi par {{ inventory_hostname_short }}</p>"
        state: present
        create: false
```

## 💡 Pièges

- **Un état, pas des commandes.** Le script Bash `echo "..." | tee -a` ajoute
  **une ligne par exécution** : c'est la dérive. Ne le traduisez **pas** en une
  tâche `command:` ou `shell:`. Décrivez l'**état** désiré avec un module qui
  sait déjà converger (`lineinfile` avec un `regexp`, ou `copy` / `template`).
  C'est tout le sens de l'exercice.
- **Le regexp de `lineinfile`.** Le `regexp` doit correspondre à **la ligne que
  vous écrivez**. Sinon, `lineinfile` ne reconnaît jamais sa propre sortie et
  rajoute une ligne à chaque passage : vous avez réinventé la dérive du Bash en
  YAML. Le `changed=0` au second passage est la preuve que c'est correct.
- **`present`, pas `latest`.** `state: latest` réinterroge le dépôt et peut
  renvoyer `changed` sur une simple mise à jour amont : c'est une dérive aussi.
  Utilisez `state: present`.
- **Pare-feu permanent.** Une règle seulement runtime disparaît au prochain
  `firewall-cmd --reload`. Mettez `permanent: true` **et** `immediate: true`.
- **FQCN.** Utilisez les noms pleinement qualifiés (`ansible.builtin.dnf`,
  `ansible.posix.firewalld`, `ansible.builtin.systemd_service`,
  `ansible.builtin.lineinfile`). `ansible-lint --profile production` l'exige.

## 🚀 Lancement

```bash
# Depuis la racine du dépôt, une fois challenge/solution.yml écrit :
ansible-playbook labs/decouvrir/declaratif-vs-imperatif/challenge/solution.yml

# Relancez-le une seconde fois : le PLAY RECAP doit afficher changed=0 partout.
ansible-playbook labs/decouvrir/declaratif-vs-imperatif/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/decouvrir/declaratif-vs-imperatif/challenge/tests/
```

La suite pytest prouve l'**état du système**, pas qu'une commande a tourné :

- `nginx` est installé, démarré et activé au boot.
- `http` est ouvert dans firewalld, en runtime **et** en permanent.
- `index.html` contient **exactement une** ligne `<p>Servi par ...</p>`.
- nginx sert réellement cette page en HTTP.
- Le playbook est **idempotent** : un second passage donne `changed=0`.

## 🧹 Remise à zéro

```bash
dsoxlab clean decouvrir-declaratif-vs-imperatif
```

Supprime la ligne « Servi par ... » pour rejouer depuis un état propre.

## 💡 Pour aller plus loin

- Rendez le script **Bash** idempotent à la main
  (`grep -q "Servi par" ... || echo ...`). Ça marche, mais vous avez réinventé
  l'idempotence pour une seule ligne. Imaginez-la sur 50 fichiers : voilà
  pourquoi le modèle déclaratif l'emporte.
- Remplacez `lineinfile` par `copy` + `content:` ou un `template`. `copy` est
  idempotent par **somme de contrôle** (le fichier entier), `lineinfile` par
  **regexp** (une ligne). Quand faut-il préférer l'un ou l'autre ?
