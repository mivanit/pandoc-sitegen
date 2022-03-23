from pandocfilters import Link,toJSONFilter

def links_md2html(key, value, format, meta) -> None:
	"""convert dendron links to markdown links"""
	if key == "Link":
		link_txt = value[1][0]
		link_tgt = value[2][0]
		if link_tgt.endswith('md'):
			return Link(
				[ "", [], [] ],
				[link_txt],
				[
					f"{link_tgt.removesuffix('md')}{'html'}",
					"",
				],
			)
		else:
			return None
	else:
		return None

if __name__ == "__main__":
	toJSONFilter(links_md2html)