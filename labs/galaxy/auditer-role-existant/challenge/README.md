# 🎯 Challenge — Audit checklist exhaustif

## ✅ Objectif

Vérifier que `AUDIT_CHECKLIST.md` (à la racine du lab) couvre **tous** les
axes d'audit production :

| Axe | Checkpoints attendus |
| --- | --- |
| Mainteneur | mention "mainteneur" / "maintainer" |
| Sécurité | mention "sécurité" / "security" + "secret" |
| Tests | "molecule" + "ansible-lint" |
| Idempotence | mention "idempotence" |
| Validation | mention "argument_specs" |
| Score | mention "score" |
| Richesse | **≥ 25 checkpoints** (lignes `- [ ]`) |

## 🧩 Indices

`AUDIT_CHECKLIST.md` est livré. Vérifiez sa richesse, ajoutez des
checkpoints si nécessaire pour atteindre les 25, puis posez `solution.sh` :

```bash
echo "Lab 75 : audit checklist validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement

Pas de playbook — c'est un challenge **documentaire**. Pour pratiquer un
audit réel :

```bash
ansible-galaxy role install geerlingguy.nginx
# Parcourir ~/.ansible/roles/geerlingguy.nginx/ et cocher la checklist
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/auditer-role-existant/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/galaxy/auditer-role-existant/ clean
```

## 💡 Pour aller plus loin

- Forker `AUDIT_CHECKLIST.md` dans vos templates internes.
- Automatiser une partie de l'audit avec `ansible-lint` + `grep` patterns.
- Intégrer la checklist au **PR template** GitHub d'un repo Ansible.
