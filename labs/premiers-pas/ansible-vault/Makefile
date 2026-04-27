# Reset du lab 04b — premiers pas ansible-vault.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime /tmp/db-config.txt et /tmp/db1-app.conf sur db1.lab
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/tmp/db-config.txt state=absent" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/tmp/db1-app.conf state=absent" 2>&1 | tail -2 || true
