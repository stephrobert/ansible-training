# Makefile du lab 02-decouvrir-installation-ansible.
# Lab local sur le control node — aucun managed node n'est sollicité.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help run verify clean

help:        ## Affiche cette aide
	@echo "Lab 02 — Installation d'Ansible (vérifications locales)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

run:         ## Affiche les 4 vérifications principales (à lire et comprendre)
	@echo "===> 1. ansible --version"
	@cd $(LAB_ROOT) && ansible --version | head -3
	@echo ""
	@echo "===> 2. Binaires Ansible standard"
	@for bin in ansible ansible-playbook ansible-galaxy ansible-doc \
	            ansible-vault ansible-config ansible-inventory ansible-lint; do \
	    command -v $$bin >/dev/null 2>&1 \
	        && echo "  ✓ $$bin" \
	        || echo "  ✗ $$bin MANQUANT"; \
	done
	@echo ""
	@echo "===> 3. Nombre de modules disponibles"
	@printf "  modules disponibles : %s\n" "$$(ansible-doc -l 2>/dev/null | wc -l)"
	@echo ""
	@echo "===> 4. Collections clés"
	@cd $(LAB_ROOT) && ansible-galaxy collection list 2>/dev/null \
	    | grep -E "ansible.posix|community.general|community.libvirt" || echo "  (aucune trouvée)"

verify:      ## Tests pytest qui valident l'installation
	@cd $(LAB_ROOT) && pytest -v $(CURDIR)/challenge/tests/

clean:       ## Pas de rollback nécessaire (lab local)
	@echo "[lab-02] Aucun rollback nécessaire (lab local)."
