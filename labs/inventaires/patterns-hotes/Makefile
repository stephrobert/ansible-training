# Reset du lab 56.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les marqueurs lab56-mark-*.txt sur tous les hôtes
	@cd $(LAB_ROOT) && ansible all -b -m ansible.builtin.shell \
	    -a "rm -f /tmp/lab56-mark-*.txt" 2>&1 | tail -5
