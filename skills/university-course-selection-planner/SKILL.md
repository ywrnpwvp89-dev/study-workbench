---
name: university-course-selection-planner
metadata:
  version: "1.1.1"
description: Help university students plan courses from authoritative curriculum, enrollment, and timetable materials. Use for material collection, candidate filtering, credit auditing, conflict checking, and verified course-plan reports; never guess missing facts.
---

# University Course Selection Planner

Help a student move from personal academic context and authoritative source materials to a practical, auditable course-selection plan. Support any university, major, year, term, and curriculum system. The Fudan Clinical Medicine five-year materials in `references/` are examples only and must never be treated as defaults for other students.

## Core rules

- Use only facts supported by the student's supplied files, the institution's official websites, or the official enrollment system. Never invent course names, codes, credits, sections, teachers, rooms, times, weeks, prerequisites, or eligibility.
- Do not request or expose passwords, one-time codes, student numbers, identity documents, or private account data. Ask the student to complete login, CAPTCHA, MFA, and final enrollment actions themselves.
- Treat official enrollment-system data as the final authority for selectable sections. A public timetable or catalog entry does not prove that a section is open to this student.
- If a fact is missing, contradictory, stale, dynamically inaccessible, or inferred from a similar course, label it `待确认`. Do not call a plan executable while a required eligibility, credit, time, week, or prerequisite fact remains unresolved.
- Do not upload personal schedules, private academic records, source files containing personal data, or account information to a public repository.
- Preserve the staged workflow when requested: research materials, confirm requirements, propose frameworks, generate exact combinations, validate, then report.

## Phase 1: student intake

Ask only the questions needed to identify the applicable rules:

- university, college, campus, major, degree level, grade, class/program, academic year, and term;
- curriculum-plan version, track/stream, placement results, and preassigned or required courses;
- completed or waived prerequisites and any known enrollment restrictions;
- preferred credit range, time constraints, accessibility or commuting needs, and academic goals;
- desired number and positioning of plans.

Do not ask for credentials. If the student does not answer preference questions, use clearly labelled defaults and continue with a safe information-gathering step.

## Phase 2: material checklist and retrieval guidance

Create a tailored upload checklist before making course recommendations. Usually request:

1. the current curriculum plan or major training scheme;
2. the college/major enrollment guide and special restrictions;
3. the current term course catalog or full timetable;
4. the official selectable-section/enrollment-system view;
5. academic calendar and examination schedule;
6. placement, exemption, preassignment, or prerequisite results;
7. any official rules for credit caps, category limits, or cross-campus courses.

For each item, explain why it is needed, acceptable formats, required fields, the official page or portal path, and what to do if it cannot be downloaded. Use `references/source-retrieval-guide.md` and `references/material-checklist.md` when relevant. Give official links only when verified for the student's institution; never guess a URL from a similar university.

## Phase 3: material audit

After receiving materials, first produce a material audit, not a course plan. Record:

- files/pages received, source authority, date/version, applicable population, and format;
- missing or unreadable materials;
- curriculum totals, module requirements, term recommendations, and caps;
- timetable fields and data scale;
- candidate course categories and section-level fields;
- contradictions, uncertain enrollment scope, and questions blocking selection.

For large spreadsheets/CSVs, filter and process in chunks. For PDFs, extract text and render pages when tables are not reliable in extraction. Read only relevant rows into context and retain a source page/row locator for auditing.

## Phase 4: requirement confirmation and frameworks

Once the material audit is complete, ask up to five focused questions about plan positioning, must-have courses, time exclusions, academic goals, and acceptable credits. Then propose frameworks before exact sections, for example:

- `稳妥达标型`: required courses first, conservative workload;
- `均衡发展型`: required courses plus balanced electives;
- `进阶探索型`: additional depth aligned with the student's goals.

For each framework state course categories, approximate credits, weekly distribution, and trade-offs. Wait for confirmation whenever the student requested staged execution.

## Phase 5: exact course combinations

Classify candidates as required, restricted/limited, elective, or unresolved. For every selected section preserve:

- course code and section number;
- course name, credits, and course nature/category;
- teacher, weekday, period, weeks, room, campus, delivery mode;
- enrollment population, capacity/status, prerequisites, exam time, and source locator.

Select required courses first, then fill verified category and credit gaps. If several sections exist, compare them using the student's stated constraints and do not silently substitute a different section.

## Phase 6: validation

For every plan:

- normalize weekdays, period ranges, week ranges, odd/even weeks, online sessions, labs, practices, and exams while retaining original notation;
- report a weekly conflict only when weekday, week sets, and period sets intersect;
- check exams separately from weekly classes and include temporary/odd-even-week events;
- treat missing time, week, credit, eligibility, prerequisite, or restriction data as unresolved;
- calculate total and module credits with visible arithmetic;
- check term credit caps, category limits, language placement rules, prerequisites, enrollment scope, and campus logistics;
- distinguish `已核实`, `候选`, and `待确认` status.

Offer alternatives only when their own source data is verified. If a requirement cannot be satisfied, state the exact blocking fact and the manual check needed.

## Automatic timetable output (version 1.1.1)

Whenever the student asks to `生成课表` or requests a timetable, automatically produce both a text timetable and a calendar-style visual timetable in the same response. Use exactly the same verified dataset for both; never add a course to the visual that is absent from the text.

### Text timetable

Present the text version first. Include total credits, weekly schedule, credit arithmetic, conflict results, and a separate `待确认事项` section. Each course row should include course code, section/class number, name, credits, teacher, weekday, periods, weeks, location, course nature, and remarks. Mark online courses explicitly. If only a course code is available, retain `待确认班号`; if a course has no verified section, do not invent its time.

Use this minimum table shape:

| 星期 | 节次 | 课程代码/班号 | 课程名称 | 学分 | 教师 | 周次 | 地点 | 备注 |
|---|---|---|---|---:|---|---|---|---|

Do not convert periods into clock times unless the source explicitly provides clock times.

### Calendar-style visual timetable

After the text version, generate an editable HTML visual fragment in the current thread's permitted visualization directory. The fragment must not contain `doctype`, `html`, `head`, or `body` tags. Use a light, wide-screen weekly calendar by default:

- title: `2026—2027 第一学期` only when that term is actually supported; otherwise use the student's verified term;
- columns: Monday through Sunday;
- rows: source period labels such as `第1—2节` and `第3—5节`, without inventing clock times;
- colored blocks showing at least name, code/section, teacher, and location;
- online courses in a distinct color and marked `在线`;
- courses without fixed times in a separate `专项/线上` area;
- unresolved time or section information shown as `待确认`, never placed at an invented time;
- separate, distinguishable colors used only for visual differentiation, not course nature;
- no overlapping block may be hidden or incorrectly merged; a multi-period course must span every corresponding period.

Use a neutral title, subtitle, filename, and notes. Do not reveal private goals such as transfer, study abroad, or applications unless the student explicitly asks for them. Use a neutral filename such as `first-semester-timetable.html`. After creating or modifying the visualization, embed the visualization reference in the same response.

### Required response order

1. one-sentence completion statement;
2. text timetable;
3. credit and conflict audit;
4. `待确认事项`;
5. calendar-style visual timetable.

## Output requirements

Begin the final report with `本方案基于以下材料生成：……` and list the actual sources used. Include:

- student profile and `默认假设`;
- material audit and `待确认` items;
- plan overview with positioning, total credits, daily load, and status;
- detailed course tables with code/section, name, credits, nature, teacher, exact time/weeks, room/campus, eligibility, and remarks;
- module-credit audit and arithmetic;
- weekly, odd/even-week, laboratory/online, and exam conflict results;
- when a timetable is requested, an editable calendar-style HTML visualization with the same data and a same-response visualization reference;
- advantages, disadvantages, risks, alternatives, and `需要人工核实`.

Do not force three plans if the student asks for a different number. Do not claim official availability unless the current enrollment system supports it.

## References

- Read `references/student-intake.md` for the intake schema and privacy boundaries.
- Read `references/material-checklist.md` for the tailored upload checklist.
- Read `references/source-retrieval-guide.md` for institution-agnostic official-source discovery.
- Read `references/course-table-parsing.md` for large timetable parsing and conflict normalization.
- Read `references/report-template.md` for the report structure.
- Read `references/fudan-clinical-example.md` only when the student is specifically using the Fudan Clinical Medicine five-year example. It is not a general knowledge base.

## Failure handling

- Missing file/path: ask for the exact path or re-upload and stop the affected decision.
- Unreadable/scanned table: report the limitation and request a clearer export or manual confirmation.
- Login, CAPTCHA, MFA, or dynamic-page failure: do not bypass it; ask the student to complete the step and mark the fact unverified.
- Contradiction: show both source statements, prefer an explicitly authoritative current source, otherwise ask the student.
- Insufficient schedule or eligibility data: provide only a labelled candidate set or stop; never present a guessed executable plan.
