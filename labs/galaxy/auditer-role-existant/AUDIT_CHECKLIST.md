# Checklist d'audit d'un rôle Ansible tiers

Avant d'utiliser un rôle Galaxy / GitHub dans votre projet, parcourir cette checklist.

## ✅ Mainteneur

- [ ] Auteur connu / organisation officielle (Red Hat, geerlingguy, ansible-collections, etc.)
- [ ] Date du dernier commit < 12 mois
- [ ] Issues récentes répondues
- [ ] CHANGELOG.md à jour avec versions

## ✅ Qualité du code

- [ ] **`meta/main.yml`** complet (galaxy_info, platforms, dependencies)
- [ ] **`meta/argument_specs.yml`** présent (validation auto des entrées)
- [ ] **`README.md`** documente toutes les variables
- [ ] FQCN partout dans `tasks/` (`ansible.builtin.dnf`, pas juste `dnf`)
- [ ] **Pas de `command:` ou `shell:`** sans `creates:`/`removes:`
- [ ] Variables préfixées par le nom du rôle (`nginx_*`, pas `version`)

## ✅ Sécurité

- [ ] Aucune **clé** ou **secret** dans le code
- [ ] Aucune URL de **download non-HTTPS** (`http://...`)
- [ ] Pas de **téléchargement sans `checksum:`**
- [ ] Permissions strictes sur les **fichiers déployés** (`mode: 0640` ou plus restrictif)
- [ ] Pas de `become_user: root` non justifié
- [ ] **Validation** des entrées via `argument_specs.yml`

## ✅ Tests

- [ ] **`molecule/`** présent avec scénario default
- [ ] **`verify.yml`** ou tests testinfra
- [ ] **`.ansible-lint`** présent (idéalement profil production)
- [ ] **CI/CD** (GitHub Actions, GitLab CI) actif

## ✅ Compatibilité

- [ ] **Platforms** déclarées dans `meta/main.yml` matchent votre environnement
- [ ] **`min_ansible_version`** ≤ votre version d'Ansible
- [ ] Pas de **dépendances obsolètes** (yum_module, etc.)

## ✅ Idempotence

- [ ] Test `molecule converge && molecule verify` retourne `changed=0` au 2e run
- [ ] Pas de **`changed_when: true`** non justifié
- [ ] Pas de **`ignore_errors: true`** sur les tâches critiques

## ✅ Maintenabilité

- [ ] Code **commenté** (au moins les sections complexes)
- [ ] Variables avec **defaults raisonnables**
- [ ] Pas de **rôle imbriqué** > 2 niveaux
- [ ] Tâches groupées par **responsabilité** (install / configure / start / verify)

## Score d'audit

- **9-10/10 sections OK** → Rôle de qualité production. Adopter.
- **7-8/10** → Acceptable avec audit complémentaire des points manquants.
- **5-6/10** → Risqué. Considérer un fork ou une alternative.
- **< 5/10** → Refuser. Trop d'effort de maintenance.
