from pandocfilters import toJSONFilter

from _link_tools import md_link_factory

if __name__ == "__main__":
	toJSONFilter(md_link_factory())