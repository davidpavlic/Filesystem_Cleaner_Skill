---
type: cleaner-report
date: {{YYYY-MM-DD}}
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
| Filesystem | Type | Size | Used | Free | Full |
|---|---|---|---|---|---|
| {{mount}} | {{ext4}} | {{size}} | {{used}} | {{free}} | {{yes/no}} |

| Largest folders | Size | Share | Reclaim command |
|---|---|---|---|
| {{path}} | {{size}} | {{share}} | {{command, or – if unknown}} |

## Structure Analysis
```
{{tree}}
```

| Outlier | Path | Interpretation |
|---|---|---|
| {{crowded}} | {{path}} | {{what it says about how the folder is used}} |

{{3–5 sentences: shape, areas, activity, conventions. Interpretation only, no recommendations.}}

## Dead Folders & Installers
| Path | Size | Last modified | Reason |
|---|---|---|---|
| {{path}} | {{size}} | {{date}} | {{e.g. installer of installed app, untouched for 2 years}} |

## Duplicates
| Keep | Duplicates | Size each |
|---|---|---|
| {{path}} | {{path}}<br>{{path}} | {{size}} |

## Structure Recommendation
**Current**
```
{{current tree}}
```

**Proposed**
```
{{proposed tree}}
```

{{2–3 sentences: why this structure}}

## Recommended Actions
<!-- Checklist so the user can tick items off. Biggest gains first. -->
- [ ] Delete `{{path}}` – {{size}}, {{reason}}
- [ ] Rename `{{old}}` → `{{new}}`
- [ ] Move `{{path}}` → `{{target}}`
