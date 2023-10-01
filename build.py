"""pandoc-sitegen

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
$$DEFAULT_CONFIG_STR$$
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

"""


import json
import time
from typing import *
import subprocess
import os
import sys
from pathlib import Path
from shutil import copytree

import yaml
import chevron  # type: ignore

RSS_TEMPLATE: str = """<rss version="0.91">
  <channel>
    <title>{title}</title>
    <link>{link}</link>
    <description>{description}</description>
    <language>en-us</language>
    {items}
  </channel>
</rss>
"""

RSS_ITEM_TEMPLATE: str = """<item>
      <title>{title}</title>
      <link>{link}</link>
      <description>{description}</description>
    </item>"""


DEFAULT_CONFIG_STR: str = """# NOTE: `!join` is a custom directive that will add the elements of the list together. useful for concatenating strings

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

# this gets merged into the frontmatter of each document (for mustache only)
frontmatter_defaults:
  __into_header__: ""
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

# whether to keep track of when the site was last built
# any file last modified prior to the saved time will not be rebuilt
# this can be overridden by passing `--rebuild` or by deleting the file at `build_time_fname`
smart_rebuild: true
build_time_fname": ".build_time"

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
"""

__doc__ = __doc__.replace("$$DEFAULT_CONFIG_STR$$", DEFAULT_CONFIG_STR)

# pylint: disable=dangerous-default-value

# define custom tag handler for yaml
# originally from
# https://stackoverflow.com/questions/5484016/how-can-i-do-string-concatenation-or-string-replacement-in-yaml#5954748
def join(loader, node):
	seq = loader.construct_sequence(node)
	return "".join([str(i) for i in seq])


# register the tag handler
yaml.add_constructor("!join", join)

# define a custom `Config` type
Config = Dict[str, Any]

def unipath(path: Path) -> str:
	"""convert any path to posix style, for printing"""
	return str(path.as_posix())


class FrontmatterKeys:
	"""read-only class of special frontmatter keys"""

	index: str = "__index__"
	index_sort_key: str = "__index_sort_key__"
	index_sort_reverse: str = "__index_sort_reverse__"
	pandoc: str = "__pandoc__"
	filename: str = "__filename__"
	children: str = "__children__"

	def __init__(self):
		raise Exception("FrontmatterKeys is a read-only class")

	def __setattr__(self, name: str, value: Any) -> None:
		raise Exception("FrontmatterKeys is a read-only class")


# define a default config
DEFAULT_CONFIG: Config = {
	FrontmatterKeys.pandoc: {
		"email-obfuscation": "references",
		"html-q-tags": True,
	},
	"content": None,
	"generated_index_suffix": "._index.md",
	"make_index_files": True,
	"mustache_rerender": True,
	"dotlist_hierarchy": True,
	"smart_rebuild": True,
	"build_time_fname": ".build_time",
	"public": None,
	"globals_key" : "__globals__",
	"extras_path": None,
	"extras_data": {},
	"resources": None,
	"default_frontmatter": {
		FrontmatterKeys.index_sort_key: "title",
		FrontmatterKeys.index_sort_reverse: False,
	},
	"site_link": None,
	"make_rss": True,
}

def update_extras(config: Config) -> None:
	"""update the globals data with mapped keys and data from `extras_path` file"""
	file_data: dict
	globals_file: Optional[str] = config.get("extras_path", None)

	# read data from file, if applicable
	if globals_file is None:
		file_data = {}
	elif not os.path.exists(globals_file):
		raise FileNotFoundError(f"globals file '{globals_file}' does not exist")
	else:
		with open(globals_file, "r", encoding="utf-8") as f:
			if globals_file.endswith(".yaml") or globals_file.endswith(".yml"):
				file_data = yaml.safe_load(f)
			elif globals_file.endswith(".json"):
				file_data = json.load(f)
			else:
				raise Exception(f"globals file '{globals_file}' is not a yaml or json file")

	# update the config with the globals
	config["extras_data"] = {
		**file_data, 
		**config.get("extras_data", {}),
	}

class PandocMarkdown(object):
	"""handles pandoc-flavored markdown and frontmatter"""

	def __init__(
		self,
		delim: str = "---",
		loader: Callable[[str], Dict] = yaml.safe_load,
		writer: Callable[[Dict], str] = lambda x: yaml.dump(
			x, default_flow_style=None, sort_keys=False
		),
	) -> None:

		self.delim: str = delim
		self.loader: Callable[[str], Dict] = loader
		self.writer: Callable[[Dict], str] = writer

		self.initialized: bool = False
		# get the first section and parse as yaml
		self.frontmatter: Dict[str, Any] = dict()
		# get the content
		self.content: str = ""

	def load_file(self, filename: Path) -> None:
		"""load a file into the pandoc markdown object

		### Parameters:
		 - `filename : Path`
		   the filename to load
		"""

		with open(filename, "r", encoding="utf-8") as f:
			# split the document by yaml file front matter
			file_text: str = f.read()
			sections: List[str] = file_text.split(self.delim)

		# check the zeroth section is empty
		if sections[0].strip():
			raise ValueError(
				f"file does not start with yaml front matter, found at start of file: {sections[0]}"
			)

		if len(sections) < 3:
			raise ValueError(f"missing sections in file {filename}, check delims")

		# get the first section and parse as yaml
		self.frontmatter = self.loader(sections[1])
		# get the content
		self.content = self.delim.join(sections[2:])

		self.initialized = True

	@staticmethod
	def create_from_file(filename: Path, **kwargs) -> "PandocMarkdown":
		pmd: PandocMarkdown = PandocMarkdown(**kwargs)
		pmd.load_file(filename)
		return pmd

	def dumps(self) -> str:
		if (self.frontmatter is None) or (self.content is None):
			raise Exception("")

		return "\n".join([
			self.delim,
			self.writer(self.frontmatter).strip(),
			self.delim,
			self.content.lstrip(),
		])

	def frontmatter_get(
		self,
		key: str, # should be a key in `FrontmatterKeys`
		defaults: Config = DEFAULT_CONFIG,
	) -> Any:
		"""get a value from the frontmatter"""
		return self.frontmatter.get(
			key,
			defaults["default_frontmatter"][key],
		)



def gen_cmd(
	plain_path: Path,
	plain_path_out: Optional[Path],
	CFG: Config,
	frontmatter: Dict[str, Any],
) -> Tuple[List[str], Path]:
	"""generate the command to run pandoc

	### Returns: `Tuple[List[str],Path]`
	 - `List[str]`
	   command to run pandoc
	 - `Path`
	   the path to the output file
	"""
	# if a different plain path not specified, use the same path as the input
	if plain_path_out is None:
		plain_path_out = plain_path
	# create the output path
	out_path: Path = Path(CFG["public"]) / Path(f"{plain_path_out}.html")

	# get the pandoc args from *both* the CFG, but override with frontmatter
	pandoc_args: Dict[str, str] = {
		**CFG["__pandoc__"],
		**(frontmatter.get(FrontmatterKeys.pandoc, dict())),
	}

	# remove entries that map to 'None'
	pandoc_args = {k: v for k, v in pandoc_args.items() if v is not None}

	# construct the base command with inputs, outputs, and paths
	md_doc_path: Path = Path(CFG["content"]) / Path(f"{plain_path}.md")

	base_cmd: List[str] = [
		"pandoc",
		"--mathjax",
		"--from", "markdown+smart",
		"--to", "html5",
		"--output", str(out_path),
		str(md_doc_path),
	]

	# add the pandoc args
	for k, v in pandoc_args.items():
		if isinstance(v, bool):
			if v:
				base_cmd.append(f"--{k}")
		elif isinstance(v, str):
			base_cmd.extend([f"--{k}", v])
		elif isinstance(v, Iterable):
			for x in v:
				base_cmd.extend([f"--{k}", x])
		else:
			base_cmd.extend([f"--{k}", v])

	return base_cmd, out_path


def get_plain_path(fname: Path, CFG: Config) -> Path:
	"""get the plain path from a filename"""

	return Path(str(fname).removesuffix(".md")).relative_to(CFG["content"])


def add_tag_page(path_original: Path, CFG: Config) -> Path:
	"""add a page which lists all pages with a given tag"""

	raise NotImplementedError()


def add_index_page(path_original: Path, CFG: Config) -> Tuple[Path, List[Dict[str, Any]]]:
	"""process an index page from `path_original` and return the new path

	new path depends on `CFG['generated_index_suffix']`

	TODO: this will only work for things organized by dotlists, not nested folders
	"""
	# create the new path
	path_new: Path = Path(
		str(path_original).removesuffix(".md") + CFG["generated_index_suffix"]
	)

	# read the existing document
	doc: PandocMarkdown = PandocMarkdown.create_from_file(path_original)

	# if we use a template from a file, append that template to the end of the content
	if "template_file" in doc.frontmatter:
		with open(doc.frontmatter["template_file"], "r", encoding="utf-8") as f:
			doc.content += f.read()

	# read the frontmatter of all downstream files (recursively)

	# ignore auto-generated pages, as well as the current page
	search_glob: str = (
		f"{path_original.stem}.*" if CFG["dotlist_hierarchy"]
		else f"{path_original.stem}/**/*.md"
	)
	downstream_pages: List[Path] = [
		p
		for p in path_original.parent.glob(search_glob)
		if (
			(not p.name.endswith(CFG["generated_index_suffix"]))
			and (p.name != path_original.name) # dont include the current file
			and (not p.is_dir())
		)
	]

	print(f"\t   found downstream pages: ", [unipath(x) for x in downstream_pages])

	# read the frontmatter for each file
	downstream_frontmatter: List[Dict[str, Any]] = list()
	for downstream_path in downstream_pages:
		# read the frontmatter
		fm_temp: Dict[str, Any] = PandocMarkdown.create_from_file(
			downstream_path
		).frontmatter
		# add the filename relative to the `content` directory
		fm_temp[FrontmatterKeys.filename] = (
			get_plain_path(downstream_path, CFG).name + ".html"
		)

		downstream_frontmatter.append(fm_temp)

	# figure out how we should sort the downstream pages
	sort_key: str = doc.frontmatter_get(FrontmatterKeys.index_sort_key)
	sort_reverse: bool = doc.frontmatter_get(FrontmatterKeys.index_sort_reverse)

	# sort the paths according to the frontmatter
	downstream_frontmatter.sort(
		key=lambda x: x.get(sort_key, ""),
		reverse=sort_reverse,
	)

	# plug the frontmatter into the content using chevron
	new_content: str = (
		"\n\n<!-- THIS IS AN AUTOMATICALLY GENERATED PAGE, CHANGES WILL BE OVERWRITTEN -->\n\n"
		+ chevron.render(
			doc.content,
			{
				**CFG["frontmatter_defaults"],
				**doc.frontmatter,
				CFG["globals_key"]: CFG,
				FrontmatterKeys.children: downstream_frontmatter,
				FrontmatterKeys.filename: path_new,
			},
			keep=True,
		)
	)

	# write the new content
	doc.content = new_content
	with open(path_new, "w", encoding="utf-8") as f:
		f.write(doc.dumps())

	# return the path of the written file so we know where to find it
	return path_new, downstream_frontmatter


def gen_page(md_path: Path, CFG: Config) -> None:
	"""generate a single page, putting it in the public directory"""
	# get the original file
	if not os.path.isfile(md_path):
		raise FileNotFoundError(f"{md_path} is not a valid source file")

	plain_path: Path = get_plain_path(md_path, CFG)
	plain_path_out: Path = plain_path
	is_index_page: bool = False
	doc: PandocMarkdown = PandocMarkdown.create_from_file(md_path)
	# add globals to the frontmatter
	# TODO: this isnt very clear, render it before reading as yaml?
	doc.frontmatter = yaml.safe_load(chevron.render(
		yaml.dump(doc.frontmatter),
		{ CFG["globals_key"]: CFG },
		keep=True,
	))

	# make the directory if needed
	os.makedirs(Path(CFG["public"]) / plain_path_out.parent, exist_ok=True)

	# if it is a special index file, generate the index page
	# NOTE: when we have an index page, we dymanically generate a sub-index page in markdown,
	#	   but only generate the html using that sub-index page
	if CFG["make_index_files"]:
		if (FrontmatterKeys.index in doc.frontmatter) and (
			doc.frontmatter[FrontmatterKeys.index]
		):
			gen_idx_path, downstream_frontmatter = add_index_page(md_path, CFG)
			plain_path = get_plain_path(gen_idx_path, CFG)
			is_index_page = True

	# construct and run the command
	cmd, out_path = gen_cmd(
		plain_path=plain_path,
		plain_path_out=plain_path_out,
		CFG=CFG,
		frontmatter=doc.frontmatter,
	)

	site_link = CFG["site_link"]
	if is_index_page and CFG["make_rss"]:
		rss_path = out_path.with_suffix(".rss")
		with open(rss_path, "w") as rss_file:
			rss_items = [
				RSS_ITEM_TEMPLATE.format(
					title=downstream_page["title"],
					link=f"{site_link}/{downstream_page[FrontmatterKeys.filename]}",
					description=downstream_page["description"],
				) for downstream_page in downstream_frontmatter
			]
			rss_file.write(
				RSS_TEMPLATE.format(
					title=doc.frontmatter["title"],
					link=site_link,
					description=doc.frontmatter["description"],
					items="\n    ".join(rss_items),
				)
			)

	p_out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if p_out.returncode != 0:
		raise RuntimeError(
			f"Failed to generate {plain_path}:\n\n{p_out.stderr.decode('utf-8')}"
		)

	# rerender the page
	do_rerender: Union[bool, int] = CFG["mustache_rerender"]
	if do_rerender:
		with open(out_path, "r", encoding="utf-8") as f:
			content: str = f.read()
		content_new: str = content
		
		for _ in range(do_rerender):
			content_new = chevron.render(
				content_new,
				{
					**CFG["frontmatter_defaults"],
					**doc.frontmatter, 
					CFG["globals_key"]: CFG,
					FrontmatterKeys.filename: out_path.name,
				},
				keep=True,
			)

		with open(out_path, "w", encoding="utf-8") as f:
			f.write(content_new)

	# if an index page, delete the auto-generated index page
	if is_index_page:
		os.remove(gen_idx_path)


def gen_all_pages(CFG: Config) -> None:
	# create all required directories first
	# REVIEW: is this needed?
	# for content_dir in Path(CFG['content']).glob('*'):
	# 	if content_dir.is_dir():
	# 		public_dir : Path = CFG['public'] / content_dir.relative_to(CFG['content'])
	# 		if not public_dir.exists():
	# 			public_dir.mkdir(parents=True)
	# 			print(f"# Created {public_dir}")

	# generate all pages

	# get the build time
	build_time: float = float("-inf")
	if CFG["smart_rebuild"] and os.path.isfile(CFG["build_time_fname"]):
		with open(CFG["build_time_fname"], "r", encoding="utf-8") as f:
			build_time = float(f.read())

	# read all content files
	content_files: Iterable[Path] = list(Path(CFG["content"]).glob("**/*.md"))

	# ignore dynamically generated ones
	content_files = [
		x for x in content_files if not x.name.endswith(CFG["generated_index_suffix"])
	]
	n_files: int = len(content_files)

	# generate
	print(
		f"# Generating {len(content_files)} pages:\n\t{[unipath(x) for x in content_files]}"
	)
	print("=" * 50)
	for idx, md_path in enumerate(content_files):
		plain_path: str = unipath(get_plain_path(md_path, CFG))

		# skip if the file is older than the build time
		if CFG["smart_rebuild"] and os.stat(md_path).st_mtime < build_time:
			print(f"\t({idx+1} / {n_files})  [unmodified]  '{plain_path}'")
			continue
		else:
			print(f"\t({idx+1} / {n_files})  [building..]  '{plain_path}'")

		gen_page(md_path, CFG)

	# write the build date
	with open(CFG["build_time_fname"], "w", encoding="utf-8") as f:
		f.write(str(time.time()))


def main(argv: List[str]) -> None:

	# check for help
	if any((x in argv) for x in ["-h", "--help", "--readme", "--README"]):
		print(__doc__)
		exit(0)

	# check if we want to print the default config
	if "--default-cfg" in argv:
		print(yaml.dump(DEFAULT_CONFIG))
		exit(0)

	# load the config file
	config_file: str = argv[1]
	CFG: Config = yaml.full_load(open(config_file, "r", encoding="utf-8"))

	# merge the config with the default config
	CFG = {
		**DEFAULT_CONFIG, 
		**CFG,
	}

	# update the globals
	update_extras(CFG)
	# validate cfg
	if CFG["make_rss"]:
		if CFG["site_link"] is None:
			raise ValueError("Config validation: `site_link` must be set to generate rss")
		if not CFG["make_index_files"]:
			raise ValueError("Config validation: `make_index_files` must be set to generate rss")

	# check for force rebuild
	if "--rebuild" in argv:
		CFG["smart_rebuild"] = False

	# TODO: checking for unknown args

	print(f"# Using config file '{config_file}', loaded data:")
	print("-" * 3)
	print(yaml.dump(CFG, default_flow_style=False, indent=2))
	print("-" * 3)

	# change the path to the location of the config file, since paths are relative to it
	# only change the dir if we are not already in the correct dir
	if os.path.dirname(config_file):
		os.chdir(os.path.dirname(config_file))

	# check the `<content>` directory exists
	if not os.path.isdir(CFG["content"]):
		raise FileNotFoundError(
			f"{CFG['content']} is not a valid directory -- should have markdown files in it"
		)
	if not os.path.isdir(CFG["resources"]):
		raise FileNotFoundError(
			f"{CFG['resources']} is not a valid directory -- should have find resources in it"
		)

	# create the `<public>` directory, if it doesn't exist
	if not os.path.isdir(CFG["public"]):
		os.mkdir(CFG["public"])

	# copy everything from the `<content>/<resources>` directory to the `<public>/<resources>` directory
	resource_dir_src: Path = Path(CFG["resources"]).relative_to(Path(CFG["content"]))
	resource_dir_dst: str = str(Path(CFG["public"]) / resource_dir_src)

	if not os.path.isdir(resource_dir_dst):
		os.mkdir(resource_dir_dst)

	print(f"# Copying resources from {CFG['resources']} to {resource_dir_dst}")
	copytree(CFG["resources"], resource_dir_dst, dirs_exist_ok=True)

	# generate all pages
	gen_all_pages(CFG)


if __name__ == "__main__":
	main(sys.argv)
