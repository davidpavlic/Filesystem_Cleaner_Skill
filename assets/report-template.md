---
type: cleaner-report
date: {{YYYY-MM-DD}}
scope: {{scanned path}}
functions: [{{disk-overview, structure, user-bloat}}]
---

<!--
Instructions for filling this template (remove all comments in the final report):
- Fill only the sections for functions that actually ran; delete the others.
- All facts (sizes, dates, hashes) come from the scripts, never estimated.
- Absolute paths, sizes human-readable (MB/GB), tables sorted by size descending.
- More than 20 rows in a table: show the top 20 and add "+ n more (x GB)".
-->

# Cleaner Report – {{YYYY-MM-DD}}

## Summary
- **Scanned:** {{n}} files in {{n}} folders, {{total size}}
- **Reclaimable:** {{size}}
- **Biggest win:** {{one sentence}}

## Disk Overview
{{If the scanned path is not on the full filesystem: say that cleaning it frees nothing there.}}

| Filesystem | Type | Size | Used | Free | Full |
|---|---|---|---|---|---|
| {{mount}} | {{ext4}} | {{size}} | {{used}} | {{free}} | {{yes/no}} |

| Largest folders | Size | Share | Reclaim command |
|---|---|---|---|
| {{path}} | {{size}} | {{share}} | {{command, or – if unknown}} |

## Structure
**Current**
```
{{current tree, max 2 levels}}
```

**Proposed**
```
{{proposed tree, max 2 levels}}
```

| From | To | Size |
|---|---|---|
| {{path}} | {{target}} | {{size}} |

{{2–3 sentences: which areas you found and why the tree fits them}}

## Dead Folders & Installers
| Path | Size | Last modified | Reason |
|---|---|---|---|
| {{path}} | {{size}} | {{date}} | {{e.g. installer of installed app, untouched for 2 years}} |

## Duplicates
| Keep | Duplicates | Size each |
|---|---|---|
| {{path}} | {{path}}<br>{{path}} | {{size}} |

## Recommended Actions
<!-- Checklist so the user can tick items off. Biggest gains first. -->
- [ ] Delete `{{path}}` – {{size}}, {{reason}}
- [ ] Rename `{{old}}` → `{{new}}`
- [ ] Move `{{path}}` → `{{target}}`
