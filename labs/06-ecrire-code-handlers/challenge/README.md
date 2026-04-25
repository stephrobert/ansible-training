# 🎯 Challenge — Deux handlers, une tâche, et flush_handlers

Vous avez écrit une tâche qui notifie un handler. Le challenge consiste à
déclencher **deux handlers depuis une seule tâche** et à forcer leur exécution
**immédiate** via `meta: flush_handlers` pour tester la nouvelle config dans
le même play.

## ✅ Objectif

Écrire `solution.yml` qui :

1. Cible `db1.lab`
2. Installe `httpd`, le démarre, l'active
3. Modifie `/etc/httpd/conf/httpd.conf` pour poser **`ServerTokens Prod`** ET
   **`ServerSignature Off`** via **deux tâches `lineinfile`**

   > **Note pédagogique** : la directive `validate: 'apachectl -t -f %s'` est
   > tentante pour rejeter une config invalide, mais elle échoue ici parce que
   > `httpd.conf` référence `/etc/httpd/conf.d/*.conf` non disponibles dans le
   > contexte de validation (le `%s` est un fichier temporaire isolé). Pour ce
   > challenge, omettez `validate:` — vous le retrouverez correctement appliqué
   > sur des configs autonomes (sshd_config, par exemple).
4. La **première tâche** (ServerTokens) notifie **deux handlers** :
   `Reload httpd` ET `Notifier journal local` (un fichier journal)
5. La **deuxième tâche** (ServerSignature) notifie uniquement `Reload httpd`
6. Après les deux modifications, force le déclenchement des handlers via
   **`meta: flush_handlers`**
7. **Teste** l'effet via `uri:` qui appelle `http://localhost` et capture
   le header `Server`

Handlers attendus :

```yaml
handlers:
  - name: Reload httpd
    ansible.builtin.systemd:
      name: httpd
      state: reloaded

  - name: Notifier journal local
    ansible.builtin.lineinfile:
      path: /var/log/ansible-handlers.log
      line: "Config httpd modifiée le {{ ansible_date_time.iso8601 }}"
      create: true
      mode: "0644"
```

## 🧩 Consignes

1. Créez `challenge/solution.yml`.
2. Lancez :

   ```bash
   ansible-playbook labs/ecrire-code/playbooks/handlers/challenge/solution.yml
   ```

3. Au **premier run**, vous voyez les **deux handlers** tourner (notifiés par
   les deux tâches).
4. Au **second run**, **aucun handler** ne tourne (`changed=0`).

## 🧪 Validation

Le script `tests/test_handlers.py` vérifie automatiquement sur **db1.lab** :

- `httpd` est installé, running, enabled
- `/etc/httpd/conf/httpd.conf` contient `ServerTokens Prod`
- `/etc/httpd/conf/httpd.conf` contient `ServerSignature Off`
- Le fichier journal `/var/log/ansible-handlers.log` existe et contient une
  entrée — preuve que le **second handler** s'est bien déclenché
- La requête HTTP `http://db1.lab` retourne **200**
- Le **header Server** dans la réponse HTTP est exactement **`Apache`**
  (sans version), preuve que `ServerTokens Prod` est appliqué (le handler
  reload a bien tourné)

```bash
pytest -v labs/ecrire-code/playbooks/handlers/challenge/tests/
```

## 🚀 Pour aller plus loin

- Refaites le challenge en utilisant **`listen:`** sur un topic
  `httpd-config-changed`. Les deux tâches notifient ce topic, et les deux
  handlers l'écoutent. Sortie identique, code plus découplé.
- Provoquez volontairement une **erreur de syntaxe** dans `httpd.conf`
  (par exemple `ServerTokens Garbage`). Le `validate:` doit empêcher
  l'écriture du fichier ET le handler ne doit **pas** être notifié.

---

Bonne chance ! 🧠
