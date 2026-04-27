LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Désinstalle nginx du rôle webserver sur db1.lab
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.systemd_service \
	    -a "name=nginx state=stopped enabled=no" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.dnf \
	    -a "name=nginx state=absent" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/usr/share/nginx/html/index.html state=absent" 2>&1 | tail -2 || true
