yet another site generator using pandoc. This one lets you use the [mustache](http://mustache.github.io/mustache.5.html) templating language to do some cool magic

# Usage:

```bash
# prints this documentation
python build.py --help 
# prints the default config as yaml (without comments)
python build.py --default-cfg
# builds according to the config
python build.py <config_path>
```

see the [example website](https://mivanit.github.io/pandoc-sitegen/)

## create a config file

First, create a config file [example: `config.yml`](example/config.yml) with the following content:
```yaml
# NOTE: `!join` is a custom directive that will add the elements of the list together. useful for concatenating strings

# base directories
# ==============================
# NOTE: these are all relative to the location of the config file!
# where the script will look for markdown files
content: &CONTENT_DIR "./content/"
# where HTML files will be generated
public: &PUBLIC_DIR "./../docs/"
# referenced only in this yaml file, for now, but could be useful as a global
resources_base: &RESOURCES_BASE "resources/"
resources: &RESOURCES_DIR !join [*CONTENT_DIR, *RESOURCES_BASE]

# global data
# ==============================
# under this key, individual documents can access the data in this file
globals_key: "__globals__"
# json or yaml from which extra data can be loaded to be globally available
extras_path: null
# data from the above will be merged with this data
extras_data:
  shuffle_script: "<script>\n  var ul = document.querySelector('ul#shuffleme');\n  for (var i = ul.children.length;\
    \ i >= 0; i--) {ul.appendChild(ul.children[Math.random() * i | 0]);}\n</script>"

# other things
# ==============================
# whether to treat files with `index: true` specially
make_index_files: true 
# dont worry about this, its for generating temporary files
generated_index_suffix: "._index.md" 

# whether to give each HTML file a final pass with the mustache renderer, 
# with the frontmatter from the markdown source passed as the context
# you can also set this to an integer if you want to re-render the templates multiple times
mustache_rerender: true 

# use dotlist hierarchy if true, folder hierarchy if false. this will mess with relative paths in the markdown files
dotlist_hierarchy: true

# pandoc stuff
# ==============================
# these items will be passed as arguments to pandoc
# - `foo: bar` will normally be passed as `--foo bar`
# - items which are "None" will not be passed as an argument, useful for disabling things from the default config
# - items which are a boolean will be passed as `--foo` if true, and not passed if false
# - items which are lists (e.g. `foo: [a, b, c]`) will be passed as `--foo a --foo b --foo c`

__pandoc__:
  include-in-header: !join [*RESOURCES_DIR, "header.html"] # passed as '--include-in-header'
  include-before-body: !join [*RESOURCES_DIR, "before-body.html"] # passed as '--include-before-body'
  include-after-body: !join [*RESOURCES_DIR, "after-body.html"] # passed as '--include-after-body'

  # these should be paths to any pandoc filters you'd like to use. 
  # if you dont have any, just have it be an empty list
  filter: 
    - "../filters/links_md2html.py"

  email-obfuscation: 'references' # options: none|javascript|references

  html-q-tags: true
```

# writing content

Now, you can create markdown pages in the `content` directory, with a dot-separated hierarchy. For example, we can have:
```
home.md
blog.md
blog.post1.md
blog.post2.md
```

or a standard folder structure, if you set `dotlist_hierarchy: false`

## index pages

If we want `blog.md` to be an index page, put `__index__: true` in the frontmatter. The body can then contain mustache syntax 

- files matching `blog.*.md` will have their frontmatter read, and their path added to the dictionary as `__filename__`
- that list of dictionaries will be passed to mustache as `__children__`

So, we might have our `blog.md` file look like:
```markdown
---
title: Blog
description: This is the blog index
__index__: true
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
- [`Pandoc`](https://pandoc.org/) for rendering markdown to html. make sure it is in your path!
- [`PyYAML`](https://pyyaml.org/), which you can install with `pip install PyYAML`
- [`chevron`](https://github.com/noahmorrison/chevron) for rendering [mustache](http://mustache.github.io/mustache.5.html) templates. The version on pypi is broken, so you'll need to install from git: `pip install git+https://github.com/noahmorrison/chevron@5e1c12827b7fc3db30cb3b24cae9a7ee3092822b`

you can also install via
```bash
pip install -r requirements.txt
```

the script is otherwise standalone. Clone the git repo if you'd like, or just download the file somewhere.


# Roadmap

Every feature I originally intended for `pandoc-sitegen` has been added, but I'm not fundamentally opposed to more features. pull requests are welcome! Some possible future features I might eventually add:

- [x] allow items to reference global items from the config and external files (see [`special.md`](content/special.md) in example site)
- [x] templating in YAML headers? (rendering with globals now applied to yaml header raw text)
  - filter locations and other paths in header are not portable, would be good to fix this
- [ ] inheriting pandoc args/config from parent items (mostly for styling different parts of a site differently)
- [ ] auto-generate tag pages
- [ ] generation of RSS files

I'd like to keep this project as a single-file script of pure python with minimal dependencies, for simplicity and portability.


# similar tools/resources:

- https://github.com/brianbuccola/brianbuccola.github.io
- https://runningcrocodile.fi/pandoc_static_site/
- http://pdsite.org/installing/
- https://github.com/locua/pandoc-python-static-site-gen
- https://github.com/lukasschwab/pandoc-blog
- https://github.com/fcanas/bake

if you end up using this script for your site and would me to list it here, email me or submit a PR :)

By [Michael Ivanitskiy](mailto:mivanits@umich.edu)
