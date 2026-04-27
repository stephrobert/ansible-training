# 🎯 Challenge — `any_errors_fatal` sans erreur réelle

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **les 2 webservers** active le mot-clé
**`any_errors_fatal: true`** au niveau du play et pose un fichier marqueur sur
chaque hôte.

> 💡 **Pourquoi sans erreur réelle ?** Tester `any_errors_fatal` en provoquant
> une erreur arrêterait le play sur les 2 hôtes — donc rien ne pourrait être
> validé par les tests. Ce challenge se contente de **valider la syntaxe** : un
> play avec `any_errors_fatal: true` qui réussit doit bien poser les fichiers
> sur **tous** les hôtes.

## 🧩 Sémantique de `any_errors_fatal`

Avec `serial:` (lab 09), si un hôte échoue, seul le batch courant s'arrête.
Avec **`any_errors_fatal: true`**, **dès qu'un hôte échoue**, **tout le play
s'arrête** — y compris pour les hôtes encore en cours sur d'autres batches.

C'est le **pattern « ne pas écrire à moitié »** : si la 1ère machine échoue,
on ne pousse même pas sur les suivantes.

## 🧩 Squelette

```yaml
---
- name: Challenge - any_errors_fatal
  hosts: ???                          # webservers
  become: ???
  any_errors_fatal: ???

  tasks:
    - name: Marqueur sans erreur sur chaque webserver
      ansible.builtin.copy:
        dest: "/tmp/anyfatal-{{ ??? }}.txt"
        content: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **Mot-clé play-level**, pas task-level : `any_errors_fatal: true` se
>   place **à la racine du play** (au même niveau que `hosts:`,
>   `become:`), pas dans une tâche.
> - **`inventory_hostname` dans `dest:`** : pour avoir un fichier par
>   hôte. Sinon les 2 webservers écrivent le même fichier — la 2ème
>   écriture écrase la 1ère, et le test cherchera 2 fichiers distincts.
> - **`any_errors_fatal` arrête TOUT** : différent de `max_fail_percentage`
>   qui tolère un seuil. Lecture officielle :
>   [doc Ansible — error handling](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_error_handling.html).
> - **Test sans erreur réelle** : ce challenge ne provoque pas d'erreur
>   exprès — tester avec `/bin/false` casserait les 2 hôtes et le test ne
>   pourrait rien valider.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/any-errors-fatal/challenge/solution.yml
```

🔍 `PLAY RECAP` : `changed=1` sur **les 2 hôtes**.

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/any-errors-fatal/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/any-errors-fatal clean
```

## 💡 Pour aller plus loin

- **`any_errors_fatal: true` + erreur** : ajoutez une tâche qui échoue sur
  web2 (ex: `command: /bin/false` avec `when: inventory_hostname == "web2.lab"`).
  Observez : l'erreur sur web2 arrête le play **même pour web1** qui n'avait
  pourtant pas terminé. Sans `any_errors_fatal`, web1 aurait fini son play.
- **Combinaison `serial: 2 + any_errors_fatal: true`** : sur 10 hôtes, si l'un
  échoue dans le batch 2 (hôtes 3-4), aucun des batches suivants (5-6, 7-8,
  9-10) ne tourne.
- **Différence avec `max_fail_percentage`** : ce dernier permet une
  **tolérance** (ex: 30 % d'échecs OK). `any_errors_fatal` est tolérance zéro.
- **Lint** :

   ```bash
   ansible-lint labs/ecrire-code/any-errors-fatal/challenge/solution.yml
   ```
