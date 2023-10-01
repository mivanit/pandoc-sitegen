.PHONY: update-readme
update-readme:
	@echo "\"real\" readme is the docstring of build.py, this updates readme.md to match"
	python build.py --help > readme.md

.PHONY: build
build:
	@echo "build the example site"
	python build.py example/config.yaml

.PHONY: clean
clean:
	@echo "clean the example site"
	rm -rf docs/

# listing targets, from stackoverflow
# https://stackoverflow.com/questions/4219255/how-do-you-get-the-list-of-targets-in-a-makefile
.PHONY: help
help:
	@echo -n "# list make targets"
	@echo ":"
	@cat Makefile | sed -n '/^\.PHONY: / h; /\(^\t@*echo\|^\t:\)/ {H; x; /PHONY/ s/.PHONY: \(.*\)\n.*"\(.*\)"/    make \1\t\2/p; d; x}'| sort -k2,2 |expand -t 30