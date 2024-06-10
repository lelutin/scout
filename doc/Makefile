PANDOC:=$(shell \
	if pandoc </dev/null 2>/dev/null; then \
		echo pandoc; \
	else \
		echo "Warning: pandoc not installed; can't generate manpages." >&2; \
		echo '@echo Skipping: pandoc'; \
	fi)

build install develop test: $(patsubst %.md,%,$(wildcard *.md))

%: %.md Makefile
	${PANDOC} -s -r markdown -w man -o $@ $<
	gzip $@

uninstall clean:
	rm -f *.tmp *.1 *.1.gz
