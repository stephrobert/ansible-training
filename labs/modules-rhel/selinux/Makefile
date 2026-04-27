# Reset du lab 45.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Reset SELinux : remet booléen off, supprime fcontext custom et /var/www/myapp
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "setsebool -P httpd_can_network_connect off; semanage fcontext -d '/var/www/myapp(/.*)?' 2>/dev/null; rm -rf /var/www/myapp; true" 2>&1 | tail -2
