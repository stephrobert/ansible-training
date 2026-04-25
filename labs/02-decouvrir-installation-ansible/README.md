# Installation d'Ansible — Vérifier votre poste de contrôle

Bienvenue dans ce lab de vérification ! 🚀

---

## 🧠 Rappel et lecture recommandée

🔗 [**Installer Ansible : pipx, mise, dnf, Execution Environment**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/installation-ansible/)

Cette page explique les 5 méthodes d'installation 2026 et la **recommandation** :

- **pipx** (méthode 1) : isolation Python utilisateur, recommandée pour un poste de contrôle individuel
- **paquet distribution `dnf` / `apt`** (méthode 2) : metapackage `ansible` qui inclut `ansible-core` + collections
- **mise** (méthode 3) : multi-version manager, pour gérer plusieurs versions d'Ansible côte à côte
- **uv tool install** (méthode 4) : alternative moderne à pipx
- **Execution Environment via ansible-navigator** (méthode 5) : reproductibilité totale (image OCI), recommandée RHCE 2026

---

## 🌟 Objectif du TP

À la fin :

1. Vérifier qu'Ansible est installé et accessible via `ansible --version`
2. Identifier la **version** d'`ansible-core` et la **provenance** (pipx ? dnf ? mise ?)
3. Vérifier que les **8 binaires standard** sont dans le `PATH`
4. Confirmer la présence des **collections principales** (`ansible.posix`, `community.general`)

---

## ⚙️ Exercices pratiques

### Exercice 1 — Quelle version d'Ansible avez-vous ?

```bash
ansible --version
```

Sortie typique attendue :

```text
ansible [core 2.20.1]
  config file = /home/bob/Projets/ansible-training/ansible.cfg
  configured module search path = [...]
  ansible python module location = /home/bob/.local/share/pipx/venvs/ansible/lib/python3.12/site-packages/ansible
  ansible collection location = /home/bob/.ansible/collections:/usr/share/ansible/collections
  executable location = /home/bob/.local/share/pipx/venvs/ansible/bin/ansible
  python version = 3.12.x
  jinja version = 3.1.4
  libyaml = True
```

Points à vérifier :

- **`core 2.18+`** (cible RHCE EX294 RHEL 9/10 — 2026)
- **`config file =`** pointe sur le `ansible.cfg` du repo (preuve que la config locale est chargée)
- **`executable location =`** identifie la méthode d'installation (`pipx`, `dnf`, `mise shims`…)

### Exercice 2 — Les 8 binaires standard sont-ils tous présents ?

```bash
for bin in ansible ansible-playbook ansible-galaxy ansible-doc ansible-vault ansible-config ansible-inventory ansible-lint; do
  command -v "$bin" || echo "$bin MANQUANT"
done
```

Tous les binaires doivent retourner un chemin. Si `ansible-lint` manque, lancez `pipx install ansible-lint` (cf. lab 03).

### Exercice 3 — Combien de modules sont disponibles ?

```bash
ansible-doc -l | wc -l
```

Vous devez obtenir **plusieurs milliers** (10 000+) si les collections communautaires sont installées. Si moins de 100, il manque des collections.

### Exercice 4 — Les collections clés sont-elles installées ?

```bash
ansible-galaxy collection list | grep -E "ansible.posix|community.general|community.libvirt"
```

Sortie attendue (extrait) :

```text
ansible.posix              2.1.0
community.general          11.4.7
community.libvirt          2.2.0
```

Si une collection manque : `ansible-galaxy collection install -r requirements.yml`.

### Exercice 5 — Vérification rapide via Make (à venir)

Une cible `make verify` automatisera ces 4 contrôles. Pour l'instant, lancez les commandes ci-dessus une par une.

---

## 🚀 Pour aller plus loin

- **Méthode mise** : créez un `.tool-versions` dans un projet test, posez `ansible 2.18.0`, et constatez le switch automatique de version quand vous entrez dans le répertoire.
- **Méthode Execution Environment** : suivez la section EE de la page MDX pour construire un EE avec `ansible-builder` et le lancer via `ansible-navigator run playbook.yml`. Comparez avec votre install locale.

---

Bonne vérification ! 🧠
