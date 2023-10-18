---
title: Projects
description: This is another index example
__index__: true
# __pandoc__:
#   include-after-body: "content/resources/after-body-shuffle.html"
---

**Here are all the projects:**

<ul id="shuffleme">

{{#__children__}}
<li>
<a href="{{__filename__}}"><b>{{& title}}</b></a>
	<em>{{description}}</em>  
	<br/>
	status: {{status}}
</li>
{{/__children__}}

</ul>

{{^__children__}}
No projects yet! :(
{{/__children__}}

{{{ __globals__.extras_data.shuffle_script }}}

If you refresh, the projects will be shuffled! this is done via including a script from the globals (with triple braces, to avoid html escaping).


Note that we have a custom `status` field in the project metadata. When using mustache, you can reference any item that appears in the frontmatter of the child file. Even if the element is missing, you should just get a blank.