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

{{description}}

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


# referencing globals

we can reference "globals" -- data from the config file, by having our template look like

```
(( {{__globals__.globals_key}}.<thing> ))
```

> note that I'm using `((` and `))` in place of double curly braces `{``{` since those are escaped by mustache.

So, we can see that:


| global key               | value                                    |
| ------------------------ | ---------------------------------------- |
| `content`                | `{{__globals__.content}}`                |
| `public`                 | `{{__globals__.public}}`                 |
| `resources`              | `{{__globals__.resources}}`              |
| `globals_key`            | `{{__globals__.globals_key}}`            |
| `extras_path`            | `{{__globals__.extras_path}}`            |
| `extras_data`            | `{{__globals__.extras_data}}`            |
| `make_index_files`       | `{{__globals__.make_index_files}}`       |
| `generated_index_suffix` | `{{__globals__.generated_index_suffix}}` |
| `mustache_rerender`      | `{{__globals__.mustache_rerender}}`      |
| `__pandoc__`             | `{{__globals__.__pandoc__}}`             |
| `extras_data.shuffle_script` | `{{__globals__.extras_data.shuffle_script}}` |


