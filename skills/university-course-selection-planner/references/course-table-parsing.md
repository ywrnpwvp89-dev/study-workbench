# Course-table parsing rules

Use this reference when extracting a large PDF or spreadsheet timetable.

## Required fields

Preserve, when present: course code, section number, course name, credits, teacher, title, weekday, period range, week set, room, campus, capacity, enrollment restrictions, remarks, exam time, exam type, and department.

## Normalization

- Keep the original Chinese weekday and period notation alongside normalized values.
- Parse ranges such as `[1-16]`, odd/even week expressions, comma-separated weeks, and online sessions without collapsing them into a single generic weekly time.
- Treat an online class, laboratory, practice session, and examination as separate schedule events.
- Treat missing weekday, period, week, room, or restriction fields as unknown.
- Preserve section suffixes such as `.01`; different sections can have different audiences and times.

## Filtering

Filter first by exact course code/category and then inspect all surrounding rows for restrictions and split groups. Do not infer that a course is open to Clinical Medicine students from its department alone. Keep a source page/row locator internally so every final row can be audited.

## Conflict rule

Two events conflict only when their weekday, week sets, and period sets intersect. A conflict check is incomplete if the timetable contains unresolved week or period data. Check final-exam times separately from weekly class times.
