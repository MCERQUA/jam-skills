---
name: file-processing
description: Process document files — PDF, Word, Excel, PowerPoint, or CSV. Routes to the right handler based on file type.
---

# File Processing Router

Check the file extension and read the appropriate sub-skill before starting work:

| File Type | Extension | Skill to Read |
|-----------|-----------|---------------|
| PDF | `.pdf` | `{baseDir}/../pdf/SKILL.md` |
| Word document | `.docx` / `.doc` | `{baseDir}/../docx/SKILL.md` |
| Excel spreadsheet | `.xlsx` / `.xls` | `{baseDir}/../xlsx/SKILL.md` |
| PowerPoint | `.pptx` / `.ppt` | `{baseDir}/../pptx/SKILL.md` |
| CSV / tabular data | `.csv` / `.tsv` | `{baseDir}/../csv-data-summarizer/SKILL.md` |

## Instructions

1. Identify the file type from the extension or user's description
2. Read the corresponding skill file listed above
3. Follow that skill's instructions for the task

If the user hasn't specified a file type yet, ask: "What type of file is this — PDF, Word, Excel, PowerPoint, or CSV?"
