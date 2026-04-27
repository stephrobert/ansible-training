# Reset du lab 38.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Disable + supprime lab-marker.service et son flag
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.shell \
	    -a "systemctl disable --now lab-marker 2>/dev/null; rm -f /etc/systemd/system/lab-marker.service /var/run/lab-marker.flag; systemctl daemon-reload; true" 2>&1 | tail -2
