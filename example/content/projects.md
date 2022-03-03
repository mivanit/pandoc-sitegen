---
title: Projects
description: This is another index example
index: true
---

**Here are all the projects:**

{{#children}}
- [**{{title}}**]({{__filename__}})  
	*{{description}}*  
	status: {{status}}  
{{/children}}

{{^children}}
No projects yet! :(
{{/children}}


Note that we have a custom `status` field in the project metadata. When using mustache, you can reference any item that appears in the frontmatter of the child file. Even if the element is missing, you should just get a blank.