# 🎯 Challenge — `serial: 1` + `max_fail_percentage`

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible le groupe `webservers` (web1.lab + web2.lab)
2. Active `serial: 1` (un hôte à la fois)
3. Active `max_fail_percentage: 0` (arrêt à la 1ère erreur)
4. Pose un fichier `/tmp/serial-{{ inventory_hostname }}.txt` contenant le
   timestamp ISO 8601 de l'exécution
5. Attend 2 secondes (pour rendre la différence de timestamp mesurable)

## 🧪 Validation

Le test pytest vérifie sur **web1.lab et web2.lab** :

- Les deux fichiers `/tmp/serial-web1.lab.txt` et `/tmp/serial-web2.lab.txt`
  existent
- Le timestamp de **web1** est **antérieur** à celui de **web2**, prouvant
  que `serial: 1` a séquentialisé l'exécution

```bash
pytest -v labs/09-ecrire-code-parallelisme-strategies/challenge/tests/
```
