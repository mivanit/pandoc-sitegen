# `pandoc-sitegen`

yet another site generator using pandoc

# Usage:

see the [example website](https://mivanit.github.io/pandoc-sitegen/)!

## create a config file

First, create a config file [example: `config.yml`](example/config.yml) with the following content:
```yaml
# base directories
# ==============================
# NOTE: these are all relative to the location of the config file!
# where the script will look for markdown files
content: &CONTENT_DIR "./content/"
# where HTML files will be generated
public: &PUBLIC_DIR "./../docs/"
# referenced only in this yaml file, for now
resources: &RESOURCES_DIR !join [*CONTENT_DIR, "resources/"]

# other things
# ==============================
make_index_files: true # whether to treat files with `index: true` specially
generated_index_suffix: "._index.md" # dont worry about this, its for generating temporary files

# whether to give each HTML file a final pass with the mustache renderer, 
# with the frontmatter from the markdown source passed as the context
mustache_rerender: true 

# pandoc stuff
# ==============================
# these items will be passed as arguments to pandoc
# note: items which are lists (e.g. `foo: [a, b, c]`) will be passed as `--foo a --foo b --foo c`
# note: `!join` is a custom directive that will add the elements of the list together. useful for concatenating strings
__pandoc__:
  include-in-header: !join [*RESOURCES_DIR, "header.html"] # passed as '--include-in-header'
  include-before-body: !join [*RESOURCES_DIR, "before-body.html"] # passed as '--include-before-body'
  include-after-body: !join [*RESOURCES_DIR, "after-body.html"] # passed as '--include-after-body'

  # these should be paths to any pandoc filters you'd like to use. 
  # if you dont have any, just have it be an empty list
  filter: 
    - "../filters/links_md2html.py"

  email-obfuscation: 'references'
```

# writing content

Now, you can create markdown pages in the `content` directory, with a dot-separated hierarchy. For example, we can have:
```
home.md
blog.md
blog.post1.md
blog.post2.md
```

## index pages

If we want `blog.md` to be an index page, put `__index__: true` in the frontmatter. The body can then contain mustache syntax 

- files matching `blog.*.md` will have their frontmatter read, and their path added to the dictionary as `__filename__`
- that list of dictionaries will be passed to mustache as `__children__`

So, we might have our `blog.md` file look like:
```markdown
---
title: Blog
description: This is the blog index
index: true
---

Here all all the blog posts:
{{#__children__}}
- [**{{title}}**]({{__filename__}})  
	*{{description}}*
{{/__children__}}

{{^__children__}}
No blog posts yet. :(
{{/__children__}}
```

## resources & assets

Won't lie, this part is kind of messy at the moment. 

Ideally, you have your assets (such as CSS, images) located in a directory under your content directory -- specified by `resources` in the config file. Then, any links to them will be preserved, since the whole directory is copied.


## building the website

simply run
```bash
python build.py <config-file>
```

this can be done from anywhere -- python will change it's working directory to the directory containing the config file. Look for your built html pages in the directory you specified as `public` in the config file!

# Installation

you will need:

- Python 3.8 or later
- [`PyYAML`](https://pyyaml.org/), which you can install with `pip install PyYAML`
- [`chevron`](https://github.com/noahmorrison/chevron) for rendering mustache templates, which you can install with `pip install chevron`
- [`Pandoc`](https://pandoc.org/) for rendering markdown to html. make sure it is in your path

the script is otherwise standalone. Clone the git repo if you'd like, or just download the file somewhere.

# similar tools/resources:

- https://github.com/brianbuccola/brianbuccola.github.io
- https://runningcrocodile.fi/pandoc_static_site/
- http://pdsite.org/installing/
- https://github.com/locua/pandoc-python-static-site-gen
- https://github.com/lukasschwab/pandoc-blog
- https://github.com/fcanas/bake