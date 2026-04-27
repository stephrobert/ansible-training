# Reset du lab 97.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime collection + roles_legacy + fichier preuve sur db1.lab
	@rm -rf $(LAB_ROOT)/labs/collections/migration-role/ansible_collections \
	        $(LAB_ROOT)/labs/collections/migration-role/roles_legacy 2>/dev/null || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/tmp/lab97-migration.txt state=absent" 2>&1 | tail -2
