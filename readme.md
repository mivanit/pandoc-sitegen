# `pandoc-sitegen`

yet another site generator using pandoc

# Usage:

see the [example website](example/)!

First, create a config file [example: `config.yml`](example/config.yml) with the following content:
```yaml
# base directories
resources: &RESOURCES_DIR "./resources/"
content: &CONTENT_DIR "./content/"
public: &PUBLIC_DIR "./public/"

# pandoc stuff
header: !join [*RESOURCES_DIR, "header.html"]
before: !join [*RESOURCES_DIR, "before-body.html"]
after: !join [*RESOURCES_DIR, "after-body.html"]
filters: []
#   - !join [*RESOURCES_DIR, "pandoc-filters/csv_code_table.py"]
#   - !join [*RESOURCES_DIR, "pandoc-filters/dendron_links_html.py"]

# index file stuff
make_index_files: true
generated_index_suffix: "._index.md"
mustache_rerender: true
```

then, run
```bash
python build.py <config-file>
```

# Installation

you will need:

- Python 3.8 or later
- [`PyYAML`](https://pyyaml.org/), which you can install with `pip install PyYAML`
- [`chevron`](https://github.com/noahmorrison/chevron) for rendering mustache templates, which you can install with `pip install chevron`
- [`Pandoc`](https://pandoc.org/) for rendering markdown

# similar tools/resources:

- https://github.com/brianbuccola/brianbuccola.github.io
- https://runningcrocodile.fi/pandoc_static_site/
- http://pdsite.org/installing/
- https://github.com/locua/pandoc-python-static-site-gen
- https://github.com/lukasschwab/pandoc-blog
- https://github.com/fcanas/bake



