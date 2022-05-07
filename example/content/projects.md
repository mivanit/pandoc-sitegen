---
title: Projects
description: This is another index example
__index__: true
---

**Here are all the projects:**

{{#__children__}}
- [**{{title}}**]({{__filename__}})  
	*{{description}}*  
	status: {{status}}  
{{/__children__}}

{{^__children__}}
No projects yet! :(
{{/__children__}}


Note that we have a custom `status` field in the project metadata. When using mustache, you can reference any item that appears in the frontmatter of the child file. Even if the element is missing, you should just get a blank.