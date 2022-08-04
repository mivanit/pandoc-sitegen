"""pandoc-sitegen

yet another site generator using pandoc
made by github.com/mivanit
project hosted at https://github.com/mivanit/pandoc-sitegen
NOTE: this docstring is just a copy of the README.md

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
make_index_files: true # whether to treat files with `__index__: true` specially
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

If we want `blog.md` to be an index page, put `index: true` in the frontmatter. The body can then contain mustache syntax 

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

"""


from typing import *
import subprocess
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from distutils.dir_util import copy_tree

import yaml
import chevron  # type: ignore

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
	FrontmatterKeys.pandoc: {"email-obfuscation": "references"},
	"content": None,
	"generated_index_suffix": "._index.md",
	"make_index_files": True,
	"mustache_rerender": True,
	"public": None,
	"resources": None,
	"default_frontmatter": {
		FrontmatterKeys.index_sort_key: "title",
		FrontmatterKeys.index_sort_reverse: False,
	},
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
			sections: List[str] = f.read().split(self.delim)

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
		"-f", "markdown",
		"-t", "html5",
		"-o", str(out_path),
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


def gen_RSS_file():
	raise NotImplementedError()


def add_index_page(path_original: Path, CFG: Config) -> Path:
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
		with open(doc.frontmatter["template_file"], "r") as f:
			doc.content += f.read()

	# read the frontmatter of all downstream files (recursively)

	# ignore auto-generated pages, as well as the current page
	downstream_pages: List[Path] = [
		p
		for p in path_original.parent.glob(f"{path_original.stem}*")
		if (
			(not p.name.endswith(CFG["generated_index_suffix"]))
			and (p.name != path_original.name)
		)
	]

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
	sort_key: str = doc.frontmatter.get(
		FrontmatterKeys.index_sort_key,
		DEFAULT_CONFIG["default_frontmatter"][FrontmatterKeys.index_sort_key],
	)
	sort_reverse: bool = doc.frontmatter.get(
		FrontmatterKeys.index_sort_reverse,
		DEFAULT_CONFIG["default_frontmatter"][FrontmatterKeys.index_sort_reverse],
	)

	# sort the paths according to the frontmatter
	downstream_frontmatter.sort(
		key=lambda x: x.get(sort_key, ""),
		reverse=sort_reverse,
	)

	# plug the frontmatter into the content using chevron
	new_content: str = (
		"\n\n<!-- THIS IS AN AUTOMATICALLY GENERATED PAGE, CHANGES WILL BE OVERWRITTEN -->\n\n"
		+ chevron.render(
			doc.content, {FrontmatterKeys.children: downstream_frontmatter}
		)
	)

	# write the new content
	doc.content = new_content
	with open(path_new, "w") as f:
		f.write(doc.dumps())

	# return the path of the written file so we know where to find it
	return path_new


def gen_page(md_path: Path, CFG: Config) -> None:
	"""generate a single page, putting it in the public directory"""
	# get the original file
	if not os.path.isfile(md_path):
		raise FileNotFoundError(f"{md_path} is not a valid source file")

	plain_path: Path = get_plain_path(md_path, CFG)
	plain_path_out: Path = plain_path
	# TODO
	is_index_page: bool = False
	doc: PandocMarkdown = PandocMarkdown.create_from_file(md_path)

	# TODO: allow for custom specification of after/before/header in frontmatter

	# if it is a special index file, generate the index page
	# NOTE: when we have an index page, we dymanically generate a sub-index page in markdown,
	#	   but only generate the html using that sub-index page
	if CFG["make_index_files"]:
		if (FrontmatterKeys.index in doc.frontmatter) and (
			doc.frontmatter[FrontmatterKeys.index]
		):
			gen_idx_path: Path = add_index_page(md_path, CFG)
			plain_path = get_plain_path(gen_idx_path, CFG)
			is_index_page = True

	# construct and run the command
	print(f"\t{plain_path}")
	cmd, out_path = gen_cmd(
		plain_path=plain_path,
		plain_path_out=plain_path_out,
		CFG=CFG,
		frontmatter=doc.frontmatter,
	)

	p_out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if p_out.returncode != 0:
		raise RuntimeError(
			f"Failed to generate {plain_path}:\n\n{p_out.stderr.decode('utf-8')}"
		)

	# rerender the page
	if CFG["mustache_rerender"]:
		with open(out_path, "r") as f:
			content: str = f.read()
		content_new: str = chevron.render(
			content,
			{**doc.frontmatter, FrontmatterKeys.filename: out_path.name},
		)
		with open(out_path, "w") as f:
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

	# read all content files
	content_files: Iterable[Path] = list(Path(CFG["content"]).glob("**/*.md"))

	# ignore dynamically generated ones
	content_files = [
		x for x in content_files if not x.name.endswith(CFG["generated_index_suffix"])
	]

	# generate
	print(
		f"# Generating {len(content_files)} pages:\n\t{[str(x) for x in content_files]}"
	)
	print("=" * 50)
	for md_path in content_files:
		gen_page(md_path, CFG)


def process_single(CFG: Config):
	"""only for testing purposes"""
	raise NotImplementedError()
	fname: str = sys.argv[1].removesuffix(".md")
	cmd, _ = gen_cmd(fname, None, CFG)
	print(" ".join(cmd))

	out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	print(out.stderr.decode("utf-8"))


def main(argv: List[str]) -> None:

	# load the config file
	if len(argv) != 2:
		raise RuntimeError("Usage: python gen.py <config_path>")

	config_file: str = argv[1]
	CFG: Config = yaml.full_load(open(config_file, "r"))

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
	copy_tree(CFG["resources"], resource_dir_dst)

	# generate all pages
	gen_all_pages(CFG)


if __name__ == "__main__":
	main(sys.argv)
