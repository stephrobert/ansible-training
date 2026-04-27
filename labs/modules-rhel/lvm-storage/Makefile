LAB_ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || (cd ../.. && pwd))

.PHONY: help clean

help:    ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

clean:   ## Démonte LVM, supprime VG/LV/PV + image loop
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.posix.mount \
	    -a "path=/mnt/lab-data state=absent" 2>&1 | tail -2 || true
	@cd $(LAB_ROOT) && ansible db1.lab -b -m ansible.builtin.shell \
	    -a "lvremove -f /dev/lab_vg/lab_lv 2>/dev/null; vgremove -f lab_vg 2>/dev/null; losetup -D 2>/dev/null; rm -f /opt/lab-lvm.img; rmdir /mnt/lab-data 2>/dev/null; true" 2>&1 | tail -2 || true
