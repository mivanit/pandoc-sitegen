"""pandoc-sitegen

yet another site generator using pandoc
made by github.com/mivanit
project hosted at https://github.com/mivanit/pandoc-sitegen

# Usage:

see the [example website](example/)!

## create a config file

First, create a config file [example: `config.yml`](example/config.yml) with the following content:
```yaml
# base directories
# ==============================
# NOTE: these are all relative to the location of the config file!
# where the script will look for markdown files
content: &CONTENT_DIR "./content/"
# where HTML files will be generated
public: &PUBLIC_DIR "./public/"
# referenced only in this yaml file, for now
resources: &RESOURCES_DIR "./resources/"

# pandoc stuff
# ==============================
# these files will be passed as arguments to pandoc
# `!join` is a custom directive that will add the elements of the list together. 
# useful for concatenating strings
header: !join [*RESOURCES_DIR, "header.html"] # passed as '--include-in-header'
before: !join [*RESOURCES_DIR, "before-body.html"] # passed as '--include-before-body'
after: !join [*RESOURCES_DIR, "after-body.html"] # passed as '--include-after-body'

# these should be paths to any pandoc filters you'd like to use. 
# if you dont have any, just have it be an empty list
filters: [] 

# other things
# ==============================
make_index_files: true # whether to treat files with `index: true` specially
generated_index_suffix: "._index.md" # dont worry about this, its for generating temporary files

# whether to give each HTML file a final pass with the mustache renderer, 
# with the frontmatter from the markdown source passed as the context
mustache_rerender: true 
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
- that list of dictionaries will be passed to mustache as `children`

So, we might have our `blog.md` file look like:
```markdown
---
title: Blog
description: This is the blog index
index: true
---

Here all all the blog posts:
{{#children}}
- [**{{title}}**]({{__filename__}})  
	*{{description}}*
{{/children}}

{{^children}}
No blog posts yet. :(
{{/children}}
```


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
"""


from typing import *
import subprocess
import os
import sys
from pathlib import Path

import yaml
import chevron

# define custom tag handler for yaml
# originally from 
# https://stackoverflow.com/questions/5484016/how-can-i-do-string-concatenation-or-string-replacement-in-yaml#5954748
def join(loader, node):
	seq = loader.construct_sequence(node)
	return ''.join([str(i) for i in seq])

# register the tag handler
yaml.add_constructor('!join', join)


class PandocMarkdown(object):
	def __init__(
			self, 
			delim : str = '---',
			loader : Callable[[str],Dict] = yaml.safe_load,
			writer : Callable[[Dict],str] = lambda x : yaml.dump(x, default_flow_style = None, sort_keys = False),
		) -> None:
		
		self.delim : str = delim
		self.loader : Callable[[str],Dict] = loader
		self.writer : Callable[[Dict],str] = writer

		self.initialized : bool = False
		# get the first section and parse as yaml
		self.frontmatter : Dict[str, Any] = dict()
		# get the content
		self.content : str = ''

	def load_file(self, filename : str) -> None:
		"""load a file into the pandoc markdown object
		
		### Parameters:
		 - `filename : str`   
		   the filename to load
		"""

		with open(filename, "r", encoding = "utf-8") as f:
			# split the document by yaml file front matter
			sections : List[str] = f.read().split(self.delim)

		# check the zeroth section is empty
		if sections[0].strip():
			raise ValueError(f"file does not start with yaml front matter, found at start of file: {sections[0]}")
		
		if len(sections) < 3:
			raise ValueError(f'missing sections in file {filename}, check delims')

		# get the first section and parse as yaml
		self.frontmatter : Dict[str, Any] = self.loader(sections[1])
		# get the content
		self.content : str = self.delim.join(sections[2:])

		self.initialized : bool = True

	@staticmethod
	def create_from_file(filename : str, **kwargs) -> 'PandocMarkdown':
		pmd : PandocMarkdown = PandocMarkdown(**kwargs)
		pmd.load_file(filename)
		return pmd

	def dumps(self) -> str:
		if (self.frontmatter is None) or (self.content is None):
			raise Exception('')

		return '\n'.join([
			self.delim,
			self.writer(self.frontmatter).strip(),
			self.delim,
			self.content.lstrip(),
		])

# yes, using globals like this is bad. I know.
CFG : Dict[str, Any] = None

def gen_cmd(plain_path : str, plain_path_out : Optional[str]) -> Tuple[List[str],Path]:
	"""generate the command to run pandoc
	
	### Returns: `Tuple[List[str],Path]`
	 - `List[str]` 
	   command to run pandoc
	 - `Path`
	   the path to the output file
	"""
	if plain_path_out is None:
		plain_path_out = plain_path

	out_path : Path = Path(CFG['public']) / Path(f'{plain_path_out}.html')

	base_cmd : List[str] = [
		'pandoc',
		# '-c', f'"{CSS}"',
		'--include-in-header', CFG['header'],
		'--include-before-body', CFG['before'],
		'--include-after-body', CFG['after'],
		'--mathjax',
		'-f', 'markdown',
		'-t', 'html5',
		'-o', out_path,
		Path(CFG['content']) / Path(f'{plain_path}.md'),
	]

	for filter_path in CFG['filters']:
		base_cmd.extend(['--filter', filter_path])

	return base_cmd, out_path


def get_plain_path(fname : Path) -> Path:
	"""get the plain path from a filename"""

	return Path(str(fname).removesuffix('.md')).relative_to(CFG['content'])

def add_index_page(path_original : Path) -> Path:
	"""process an index page from `path_original` and return the new path
	
	new path depends on `CFG['generated_index_suffix']`

	TODO: this will only work for things organized by dotlists, not nested folders
	"""
	# create the new path
	path_new : Path = Path(str(path_original).removesuffix('.md') + CFG['generated_index_suffix'])
	
	# read the existing document
	doc : PandocMarkdown = PandocMarkdown.create_from_file(path_original)

	# if we use a template from a file, append that template to the end of the content
	if 'template_file' in doc.frontmatter:
		with open(doc.frontmatter['template_file'], 'r') as f:
			doc.content += f.read()

	# read the frontmatter of all downstream files

	downstream_pages : List[str] = path_original.parent.glob(f'{path_original.stem}*')
	# ignore auto-generated pages, as well as the current page
	downstream_pages = [
		p
		for p in downstream_pages 
		if (
			(not p.name.endswith(CFG['generated_index_suffix']))
			and (p.name != path_original.name)
		)
	]
	
	# read the frontmatter for each file
	downstream_frontmatter : List[Dict[str,Any]] = list()
	for downstream_path in downstream_pages:
		# read the frontmatter
		fm_temp : Dict[str,Any] = PandocMarkdown.create_from_file(downstream_path).frontmatter
		# add the filename relative to the `content` directory
		fm_temp['__filename__'] = get_plain_path(downstream_path).name + '.html'

		downstream_frontmatter.append(fm_temp)

	# TODO: sorting functions for organizing the items in the index pages
	
	# plug the frontmatter into the content using chevron
	new_content : str = (
		'\n\n<!-- THIS IS AN AUTOMATICALLY GENERATED PAGE, CHANGES WILL BE OVERWRITTEN -->\n\n'
		+ chevron.render(doc.content, { 'children': downstream_frontmatter })
	)

	# write the new content
	doc.content = new_content
	with open(path_new, 'w') as f:
		f.write(doc.dumps())

	# return the path of the written file so we know where to find it
	return path_new




def gen_page(md_path : str) -> None:
	"""generate a single page, putting it in the public directory"""
	# get the original file
	if not os.path.isfile(md_path):
		raise FileNotFoundError(f"{md_path} is not a valid source file")
	
	plain_path : str = get_plain_path(md_path)
	plain_path_out : Optional[str] = plain_path
	is_index_page : bool = False
	doc : PandocMarkdown = PandocMarkdown.create_from_file(md_path)

	# TODO: allow for custom specification of after/before/header in frontmatter
	
	# if it is a special index file, generate the index page
	# NOTE: when we have an index page, we dymanically generate a sub-index page in markdown,
	#       but only generate the html using that sub-index page
	if CFG['make_index_files']:
		if ('index' in doc.frontmatter) and (doc.frontmatter['index']):
			gen_idx_path : str = add_index_page(Path(md_path))
			plain_path = get_plain_path(gen_idx_path)
			is_index_page = True

	# construct and run the command
	print(f"# Generating {plain_path}")
	cmd, out_path = gen_cmd(plain_path, plain_path_out)
	p_out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if p_out.returncode != 0:
		raise RuntimeError(f"Failed to generate {plain_path}:\n\n{p_out.stderr.decode('utf-8')}")

	# rerender the page
	if CFG['mustache_rerender']:
		with open(out_path, 'r') as f:
			content : str = f.read()
		content_new : str = chevron.render(content, {**doc.frontmatter, '__filename__': out_path.name})
		with open(out_path, 'w') as f:
			f.write(content_new)
	
	# if an index page, delete the auto-generated index page
	if is_index_page:
		os.remove(gen_idx_path)

def gen_all_pages() -> None:
	# create all required directories first
	# REVIEW: is this needed?
	for content_dir in Path(CFG['content']).glob('*'):
		if content_dir.is_dir():
			public_dir : Path = CFG['public'] / content_dir.relative_to(CFG['content'])
			if not public_dir.exists():
				public_dir.mkdir(parents=True)
				print(f"# Created {public_dir}")

	# generate all pages

	# read all content files
	content_files : Iterable[Path] = list(Path(CFG['content']).glob('**/*.md'))
	
	# ignore dynamically generated ones
	content_files = [
		x 
		for x in content_files 
		if not x.name.endswith(CFG['generated_index_suffix'])
	]
	
	# generate
	print(f"# Generating {len(content_files)} pages:\n\t{[str(x) for x in content_files]}")
	for md_path in content_files:
		gen_page(md_path)


def process_single():
	"""only for testing purposes"""
	fname : str = sys.argv[1].removesuffix('.md')
	cmd, _ = gen_cmd(fname)
	print(' '.join(cmd))

	out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	print(out.stderr.decode('utf-8'))


if __name__ == "__main__":
	
	# load the config file
	config_file : str = sys.argv[1]
	CFG = yaml.full_load(open(config_file, 'r'))
	
	# change the path to the location of the config file, since paths are relative to it
	os.chdir(os.path.dirname(config_file))

	# generate all pages
	gen_all_pages()



