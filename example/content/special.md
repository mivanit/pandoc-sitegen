---
title: Special Page
description: special frontmatter features
__pandoc__:
  include-before-body: null
  toc: True
  filter:
  - "../filters/links_md2html.py"
  - "../filters/csv_code_table.py"
---


# excluding includes

Note that this page is missing the nav bar! we did this by adding to the frontmatter:
```yaml
__pandoc__:
  include-before-body: null
  ...
```
which means that the `--include-before-body` option will not be passed to pandoc.


# adding a table of contents

We have also set `toc: True` in the frontmatter (under `__pandoc__`). This will be passed as `--toc` to pandoc.


# adding a csv code table
```yaml
__pandoc__:
  filter:
  - "../filters/links_md2html.py"
  - "../filters/csv_code_table.py"
  ...
```
note that we must re-include the `links_md2html.py` filter, because specifying a filter will overwrite existing filters. But, the path is still relative to our `config.yml` file.

This lets us create a table:

```{.csv_table aligns="LCR" caption="This is the caption" header=1}  
Fruit, Quantity, Price  
apples, 15, 3.24  
oranges, 12, 2.22  
```