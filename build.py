from typing import *
import subprocess
import os
import sys
from pathlib import Path


RESOURCES_DIR : Path = Path('./resources')
# CSS : str = f"{RESOURCES_DIR}/mystyle.css"
HEADER : Path = RESOURCES_DIR / "header.html"
BEFORE : Path = RESOURCES_DIR / "before-body.html"
AFTER : Path = RESOURCES_DIR / "after-body.html"
FILTERS : List[str] = [
	RESOURCES_DIR / "pandoc-filters/csv_code_table.py",
	RESOURCES_DIR / "pandoc-filters/dendron_links_html.py",
]

CONTENT_DIR : Path = Path('content')
PUBLIC_DIR : Path = Path('public')


def gen_cmd(plain_path : str) -> List[str]:
	"""generate the command to run pandoc"""
	base_cmd : List[str] = [
		'pandoc',
		# '-c', f'"{CSS}"',
		'--include-in-header', HEADER,
		'--include-before-body', BEFORE,
		'--include-after-body', AFTER,
		'--mathjax',
		'-f', 'markdown',
		'-t', 'html5',
		'-o', PUBLIC_DIR / Path(f'{plain_path}.html'),
		CONTENT_DIR / Path(f'{plain_path}.md'),
	]

	for filter_path in FILTERS:
		base_cmd.append('--filter')
		base_cmd.append(filter_path)

	return base_cmd


def gen_page(md_path : str) -> None:
	"""generate a single page, putting it in the public directory"""
	# get the original file
	if not os.path.isfile(md_path):
		raise FileNotFoundError(f"{md_path} is not a valid source file")
	plain_path : str = Path(str(md_path).removesuffix('.md')).relative_to(CONTENT_DIR)
	print(f"# Generating {plain_path}")
	# construct and run the command
	cmd : List[str] = gen_cmd(plain_path)
	out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if out.returncode != 0:
		raise RuntimeError(f"Failed to generate {plain_path}:\n\n{out.stderr.decode('utf-8')}")

def gen_all_pages() -> None:
	# create all required directories first
	for content_dir in CONTENT_DIR.glob('*'):
		if content_dir.is_dir():
			public_dir : Path = PUBLIC_DIR / content_dir.relative_to(CONTENT_DIR)
			if not public_dir.exists():
				public_dir.mkdir(parents=True)
				print(f"# Created {public_dir}")

	# generate all pages
	content_files : Iterable[Path] = [*CONTENT_DIR.glob('**/*.md')]
	print(f"# Generating {len(content_files)} pages:\n\t{[str(x) for x in content_files]}")
	for md_path in content_files:
		gen_page(md_path)


def process_single():
	"""only for testing purposes"""
	fname : str = sys.argv[1].removesuffix('.md')
	cmd : List[str] = gen_cmd(fname)
	print(' '.join(cmd))

	out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	print(out.stderr.decode('utf-8'))


# def create_research_page(path : Path):
# 	"""reads yaml header from original research markdown page, gets the corresponding bibtex, and compiles it all"""
# 	# get the original file
# 	if not os.path.isfile(path):
# 		raise FileNotFoundError(f"{path} is not a valid source file")
# 	plain_path : str = Path(str(path).removesuffix('.md')).relative_to(CONTENT_DIR)
# 	print(f"# Generating {plain_path}")
# 	# construct and run the command
# 	cmd : List[str] = gen_cmd(plain_path)
# 	cmd.append('--bibliography')
# 	cmd.append(RESOURCES_DIR / 'bibtex/bibtex.bib')
# 	out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 	if out.returncode != 0:
# 		raise RuntimeError(f"Failed to generate {plain_path}:\n\n{out.stderr.decode('utf-8')}")


if __name__ == "__main__":
	gen_all_pages()



