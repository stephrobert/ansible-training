# Reset du lab 36.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Désinstalle vim-enhanced, bash-completion, tree (et réinstalle telnet pour rejouer)
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.dnf \
	    -a "name=vim-enhanced,bash-completion,tree state=absent" 2>&1 | tail -2
