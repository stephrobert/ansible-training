# Reset du lab 40.

LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Supprime les users alice/bob/deploy + groupe rhce-team sur db1
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "userdel -r alice 2>/dev/null; userdel -r bob 2>/dev/null; userdel -r deploy 2>/dev/null; rm -rf /opt/deploy; groupdel rhce-team 2>/dev/null; true" 2>&1 | tail -2
