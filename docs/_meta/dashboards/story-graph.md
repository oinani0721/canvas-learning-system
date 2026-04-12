# Story Relationship Graph

Shows incoming/outgoing links per Story. Orphan stories (inlinks=0) surface first.

```dataview
TABLE epic_id, length(file.inlinks) as "Inlinks", length(file.outlinks) as "Outlinks", status
FROM "stories" OR "_bmad-output/implementation-artifacts"
WHERE doc_type = "story"
SORT length(file.inlinks) ASC, epic_id ASC, story_id ASC
```
