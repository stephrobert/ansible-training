# Makefile du lab 03-decouvrir-prise-en-main-cli.
# Lab local — démontre les 8 commandes Ansible.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help run verify clean

help:        ## Affiche cette aide
	@echo "Lab 03 — Prise en main de la CLI Ansible"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

run:         ## Démontre les 8 commandes en chaîne
	@echo "===> 1. ansible : ad-hoc ping"
	@cd $(LAB_ROOT) && ansible all -m ansible.builtin.ping 2>&1 | head -8
	@echo ""
	@echo "===> 2. ansible-doc : lister modules"
	@printf "  modules : %s | premiers 5 :\n" "$$(ansible-doc -l 2>/dev/null | wc -l)"
	@ansible-doc -l 2>/dev/null | head -5
	@echo ""
	@echo "===> 3. ansible-config : paramètres modifiés"
	@cd $(LAB_ROOT) && ansible-config dump --only-changed 2>&1 | head -10
	@echo ""
	@echo "===> 4. ansible-inventory --graph"
	@cd $(LAB_ROOT) && ansible-inventory --graph 2>&1
	@echo ""
	@echo "===> 5. ansible-galaxy collection list (extrait)"
	@cd $(LAB_ROOT) && ansible-galaxy collection list 2>/dev/null | head -10
	@echo ""
	@echo "===> 6. ansible-lint sur le playbook 000"
	@cd $(LAB_ROOT) && ansible-lint labs/bootstrap/prepare-managed-nodes/playbook.yml 2>&1 | head -10 || true

verify:      ## Tests pytest qui valident le challenge ansible-vault
	@cd $(LAB_ROOT) && pytest -v $(CURDIR)/challenge/tests/

clean:       ## Pas de rollback (lab local)
	@echo "[lab-03] Aucun rollback nécessaire."
