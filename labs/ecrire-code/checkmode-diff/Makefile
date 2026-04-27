# Makefile utilitaire du lab 08 — uniquement pour le reset.
# L'apprenant écrit lui-même `lab.yml` et `challenge/solution.yml`.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les fichiers posés par le lab/challenge sur les managed nodes
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.shell \
	    -a "rm -f /tmp/lab-shell-output.txt" 2>&1 | tail -2
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/etc/lab-checkmode.txt state=absent" 2>&1 | tail -2
