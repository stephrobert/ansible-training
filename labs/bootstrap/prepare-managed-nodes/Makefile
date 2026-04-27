# Makefile du lab bootstrap/prepare-managed-nodes (lab démo).
# Cibles : setup → run → verify → clean

LAB_ROOT  := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))
INVENTORY := $(LAB_ROOT)/inventory/hosts.yml
PLAYBOOK  := $(CURDIR)/playbook.yml

.PHONY: setup run verify clean help

help:        ## Affiche cette aide
	@echo "Lab 000 — Préparation des managed nodes"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:       ## Pré-requis (rien ici, le lab démarre directement après make provision)
	@echo "[lab-000] Aucun setup nécessaire — managed nodes vierges depuis cloud-init."

run:         ## Exécute le playbook de préparation
	cd $(LAB_ROOT) && ansible-playbook $(PLAYBOOK) | tee $(CURDIR)/expected-output.tmp

verify:      ## Tests pytest+testinfra (vérifient l'état post-run)
	cd $(LAB_ROOT) && pytest -v $(CURDIR)/challenge/tests/
	# Idempotence : second run doit afficher changed=0
	cd $(LAB_ROOT) && ansible-playbook $(PLAYBOOK) | grep -qE "changed=0\b" \
	    && echo "[lab-000] OK idempotent" \
	    || (echo "[lab-000] FAIL — playbook pas idempotent" && exit 1)

clean:       ## Pas de rollback (les paquets et l'horloge sont des prérequis durables du lab)
	@rm -f $(CURDIR)/expected-output.tmp
	@echo "[lab-000] Aucun rollback nécessaire (prérequis durables)."
