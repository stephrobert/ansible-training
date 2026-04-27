LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Stop httpd, restaure Listen 80, supprime /var/www/html/index.html
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.systemd_service \
	    -a "name=httpd state=stopped" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.lineinfile \
	    -a "path=/etc/httpd/conf/httpd.conf regexp='^Listen ' line='Listen 80'" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.file \
	    -a "path=/var/www/html/index.html state=absent" 2>&1 | tail -2 || true
