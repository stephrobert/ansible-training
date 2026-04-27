LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les rôles/collections vendorisés temporairement
	@rm -rf /tmp/roles /tmp/collections 2>/dev/null || true
	@rm -rf $(LAB_ROOT)/labs/galaxy/installer-roles/roles/geerlingguy.* 2>/dev/null || true
	@rm -rf $(LAB_ROOT)/labs/galaxy/installer-roles/roles/stephrobert.* 2>/dev/null || true
	@echo "Vendoring temporaire nettoyé."
