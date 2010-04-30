PANDOC:=$(shell \
	if pandoc </dev/null 2>/dev/null; then \
		echo pandoc; \
	else \
		echo "Warning: pandoc not installed; can't generate manpages." >&2; \
		echo '@echo Skipping: pandoc'; \
	fi)
SCOUT_VERSION:=$(shell \
	grep SCOUT_VERSION ../src/scout/version.py | \
	sed -e 's/^[^"]*"//' -e 's/".*$$//')
SCOUT_DATE:=$(shell \
	grep SCOUT_DATE ../src/scout/version.py | \
	sed -e 's/^[^"]*"//' -e 's/".*$$//')

build install develop test: $(patsubst %.md,%,$(wildcard *.md))

%: %.md.tmp Makefile
	${PANDOC} -s -r markdown -w man -o $@ $<
	gzip $@

.PRECIOUS: %.md.tmp
%.md.tmp: %.md Makefile
	sed -e 's,%SCOUT_VERSION%,${SCOUT_VERSION},g' \
	    -e 's,%SCOUT_DATE%,${SCOUT_DATE},g' <$< >$@

uninstall clean:
	rm -f *.tmp *.1 *.1.gz
