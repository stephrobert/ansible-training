# Reset du lab 31.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime banner-rhce / motd-rhce et leurs backups sur web1
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.shell \
	    -a "rm -f /etc/ssh/banner-rhce* /etc/motd-rhce*" 2>&1 | tail -2
