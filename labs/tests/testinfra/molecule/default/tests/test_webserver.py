"""Tests testinfra du rôle webserver : À COMPLÉTER PAR VOS SOINS.

Ces tests s'exécutent contre l'instance Molecule via la fixture `host`
de testinfra. Écrivez au moins 4 fonctions de test qui prouvent l'état
du serveur après converge :

  1. le paquet nginx est installé,
  2. le service nginx est démarré ET activé au boot,
  3. nginx écoute sur le port 8080 (variable webserver_listen_port),
  4. la configuration est valide (`nginx -t` retourne 0).

API utile : host.package(), host.service(), host.socket(), host.file(),
host.run(). Documentation : https://testinfra.readthedocs.io/
"""


def test_a_ecrire(host):
    raise NotImplementedError("Remplacez ce squelette par vos tests testinfra")
