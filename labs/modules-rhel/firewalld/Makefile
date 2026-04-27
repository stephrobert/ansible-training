# Reset du lab 44.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Retire http/https et 8080/8443 de firewalld sur web1
	@cd $(LAB_ROOT) && ansible web1.lab -b -m ansible.builtin.shell \
	    -a "firewall-cmd --permanent --remove-service=http; firewall-cmd --permanent --remove-service=https; firewall-cmd --permanent --remove-port=8080/tcp; firewall-cmd --permanent --remove-port=8443/tcp; firewall-cmd --reload; true" 2>&1 | tail -2
