# Reset du lab 32.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime l'arborescence /opt/myapp + marqueurs sur web1
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.shell \
	    -a "rm -rf /opt/myapp /var/log/myapp-init.timestamp /etc/myapp-old.conf" 2>&1 | tail -2
