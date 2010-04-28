PANDOC:=$(shell \
	if pandoc </dev/null 2>/dev/null; then \
		echo pandoc; \
	else \
		echo "Warning: pandoc not installed; can't generate manpages." >&2; \
		echo '@echo Skipping: pandoc'; \
	fi)
TOMTOM_VERSION:=$(shell \
	grep TOMTOM_VERSION ../src/tomtom/__init__.py | \
	sed -e 's/^[^"]*"//' -e 's/".*$$//')
TOMTOM_DATE:=$(shell \
	grep TOMTOM_DATE ../src/tomtom/__init__.py | \
	sed -e 's/^[^"]*"//' -e 's/".*$$//')

build install develop test: $(patsubst %.md,%,$(wildcard *.md))

%: %.md.tmp Makefile
	${PANDOC} -s -r markdown -w man -o $@ $<
	gzip $@

.PRECIOUS: %.md.tmp
%.md.tmp: %.md Makefile
	sed -e 's,%TOMTOM_VERSION%,${TOMTOM_VERSION},g' \
	    -e 's,%TOMTOM_DATE%,${TOMTOM_DATE},g' <$< >$@

uninstall clean:
	rm -f *.tmp *.1
