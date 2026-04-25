#!/bin/bash
# Script Bash impératif "naïf" — installe nginx, ouvre le port 80, démarre le service,
# personnalise la page d'accueil.
#
# Le piège pédagogique : la dernière étape n'est PAS idempotente.
# Un second run duplique la ligne dans index.html. C'est le cas typique
# du Bash qui dérive à chaque relance.

set -euo pipefail

echo "[1/4] Installation du paquet nginx..."
sudo dnf install -y nginx

echo "[2/4] Ouverture du port 80 dans firewalld..."
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload

echo "[3/4] Démarrage et activation du service nginx..."
sudo systemctl enable --now nginx

echo "[4/4] Personnalisation de la page d'accueil (PIÈGE non idempotent)..."
echo "<p>Servi par $(hostname)</p>" | sudo tee -a /usr/share/nginx/html/index.html >/dev/null

echo ""
echo "OK : nginx déployé. Occurrences de 'Servi par' dans la page :"
curl -s http://localhost/ | grep -c "Servi par" || true
