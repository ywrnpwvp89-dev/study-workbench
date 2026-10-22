# University Course Selection Planner 1.1.1

帮助高校学生根据官方培养方案、选课规则、课程表和可选教学班，制定有来源、有学分核对、无时间冲突的选课方案。

## What it does

This Skill first collects the student's academic context, then gives a tailored list of materials to upload and official retrieval paths. It audits the materials, filters candidate sections, checks weeks/periods and credit modules, and produces labelled plans with risks and manual-verification items. When asked to generate a timetable, it automatically produces both a text timetable and a calendar-style editable visualization using the same data.

## Use cases

- Plan any term for an undergraduate or other university student.
- Compare conservative, balanced, and goal-oriented course combinations.
- Audit whether a proposed combination meets curriculum credits and timetable constraints.
- Convert official course-table data into a human-readable Markdown report.

## How it works

```text
Research → Confirm needs → Frameworks → Filter → Combine → Validate → Report
```

The workflow does not generate exact plans during research. Missing or contradictory facts are marked `待确认`; no course is treated as selectable merely because it appears in a timetable.

## Installation

Clone or copy this directory into the Skill directory supported by your Codex environment. The required entrypoint is `SKILL.md`; `agents/openai.yaml` provides optional UI metadata.

```bash
git clone YOUR_REPOSITORY_URL
```

The exact Skill installation location is environment-specific; do not assume a global path.

## Example prompts

```text
Use $university-course-selection-planner-1.1.1. Ask me for my university, major, year, term, goals, and required courses, then tell me which official materials to upload. Do not generate a plan yet.
```

```text
Use $university-course-selection-planner-1.1.1 after the material audit. Ask me no more than five questions about goals, required courses, time restrictions, and acceptable credit load.
```

```text
Use $university-course-selection-planner-1.1.1 to build three concrete plans. Every row must include exact code, section, credits, teacher, time/weeks, room, and enrollment remarks from authoritative sources. If I ask for a timetable, include both the text version and calendar-style visualization.
```

## Repository structure

| Path | Purpose |
|---|---|
| `SKILL.md` | Course-planning workflow, rules, and output contract |
| `agents/openai.yaml` | Optional Codex UI metadata |
| `AGENTS.md` | Maintenance instructions for coding agents |
| `references/` | Intake, material checklist, source retrieval, parsing, examples, and report template |

## Requirements and limitations

- Requires the student's current curriculum plan, enrollment guidance, and course timetable; the official site/system is used for cross-checking.
- Course availability, seat limits, enrollment scope, and last-minute changes must still be checked in the official enrollment system/eHall.
- The Fudan Clinical Medicine material in `references/fudan-clinical-example.md` is an example only and must not be applied to other institutions.
- The Skill does not enroll the student or submit any enrollment transaction.

## Development

Edit `SKILL.md` and references, then run the Skill Creator validator from the local Skill Creator package. Test with redacted representative course rows and manually inspect credit and conflict arithmetic. Never commit personal course files.

## License

MIT. See [LICENSE](LICENSE).
