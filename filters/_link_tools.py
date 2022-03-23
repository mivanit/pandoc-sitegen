"""copied from https://github.com/mivanit/dendron-pandoc

By [@mivanit](mivanit.github.io)"""

from ast import Call
from typing import *
import re

from pandocfilters import toJSONFilter, Str, Link

class LinkRegexPattern(object):
	def __init__(
			self,
			name : str,
			regex_raw : str,
			link_group_idx : int,
		) -> None:

		self.name = name
		self.regex_raw = regex_raw
		self.link_group_idx = link_group_idx
		self.pattern = re.compile(regex_raw)

LINK_REGEXS : Dict[str,LinkRegexPattern] = {
	'md' : LinkRegexPattern(
		name = 'md',
		regex_raw = r'\[(.*?)\]\((.*?)\)',
		link_group_idx = 2,
	),
	'dendron' : LinkRegexPattern(
		name = 'dendron',
		regex_raw = r'\[\[(.*?)\]\]',
		link_group_idx = 1,
	),
	# 'html' : LinkRegexPattern(
	# 	name = 'html',
	# 	regex_raw = r'<a href="(.*?)">(.*?)</a>',
	# 	link_group_idx = 1,
	# ),
}

DENDRON_LINK_REGEX : LinkRegexPattern = LINK_REGEXS['dendron']

def get_dendron_link(data : str) -> Union[str,None]:
	"""check if the given data is a dendron link
	
	if no link exists, return `None`
	otherwise, return the link text
	"""

	match : re.Match = DENDRON_LINK_REGEX.pattern.match(data)
	if match:
		return match.group(DENDRON_LINK_REGEX.link_group_idx) 
	else:
		return None

def get_markdown_link(data : str) -> Union[str,None]:
	"""check if the given data is a markdown link

	if no link exists, return `None`
	otherwise, return a tuple
		(link text, link target)
	"""
	match : re.Match = LINK_REGEXS['md'].pattern.match(data)
	if match:
		return (match.group(1), match.group(2))
	else:
		return None

def convert_dlink_factory(
		linktext_gen : Callable = lambda x : x.split('.')[-1],
		pref : str = '', 
		ext : str = 'md',
	) -> Callable:
	
	def convert(link : str) -> str:
		return Link(
			[ "", [], [] ],
			[Str(linktext_gen(link))],
			[
				f"{pref}{link}.{ext}",
				"",
			],
		)
	
	return convert


def convert_md_link_factory(new_ext : str = 'html', old_ext : str = 'md') -> Callable:
	def convert(link_txt : str, link_tgt : str) -> str:
		return Link(
			[ "", [], [] ],
			[Str(link_txt)],
			[
				f"{link_tgt.removesuffix(old_ext)}{new_ext}",
				"",
			],
		)
	
	return convert

def md_link_factory(new_ext : str = 'html', old_ext : str = 'md') -> Callable:
	converter = convert_md_link_factory(
		new_ext = new_ext,
		old_ext = old_ext,
	)

	def filter(		
			key : Any,
			value : Any,
			format : Any,
			meta : Any,
		) -> None:
		"""convert dendron links to markdown links"""
		
		# if its a plain string
		if key == "Str":
			mlink : Optional[str, Tuple[str,str]] = get_markdown_link(value)
			if mlink is not None:
				output = converter(*mlink)

				return output
		else:
			return None

	return filter

def dendron_to_markdown_factory(
		linktext_gen : Callable = lambda x : x.split('.')[-1],
		pref : str = '', 
		ext : str = 'md',
	) -> Callable:

	converter = convert_dlink_factory(
		linktext_gen = linktext_gen,
		pref = pref,
		ext = ext,
	)

	def filter(		
			key : Any,
			value : Any,
			format : Any,
			meta : Any,
		) -> None:
		"""convert dendron links to markdown links"""
		
		# if its a plain string
		if key == "Str":
			dlink : Optional[str] = get_dendron_link(value)
			if dlink:
				output = converter(dlink)

				return output
		else:
			return None

	return filter


if __name__ == '__main__':
	raise Exception("this is a module")
