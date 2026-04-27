# Reset du lab lineinfile.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Restaure sshd_config et sysctl.conf sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "test -f /etc/ssh/sshd_config.bak && cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config && systemctl restart sshd; sed -i '/^net.ipv4.ip_forward=1$$/d' /etc/sysctl.conf" 2>&1 | tail -2
