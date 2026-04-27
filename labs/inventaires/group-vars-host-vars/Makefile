# Reset du lab 55.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les marqueurs lab55-port-*.txt sur les webservers
	@cd $(LAB_ROOT) && ansible webservers -b -m ansible.builtin.shell \
	    -a "rm -f /tmp/lab55-port-*.txt" 2>&1 | tail -3
