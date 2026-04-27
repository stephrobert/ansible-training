# Reset du lab 21.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les users challenge + le fichier récap sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.user \
	    -a "name={{ item }} state=absent remove=yes" -e '{"items":["chal_alice","chal_bob","chal_charlie"]}' 2>&1 | tail -3 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "userdel -r chal_alice 2>/dev/null; userdel -r chal_bob 2>/dev/null; userdel -r chal_charlie 2>/dev/null; rm -f /tmp/loop-result.txt; true" 2>&1 | tail -2
