# Project Instructions

## Project

This repository contains a Codex Skill for evidence-based university course planning across institutions and programs. Fudan Clinical Medicine five-year materials are examples only.

## Architecture

- `SKILL.md`: runtime course-planning workflow, domain rules, and output contract.
- `agents/openai.yaml`: UI metadata and default invocation prompt.
- `references/`: intake, material checklist, official-source retrieval, parsing rules, examples, report template, and release checklist.
- `README.md`: public installation, usage, scope, and limitations.

## Development principles

- Keep the Skill self-contained and independent of the student's chat history or private files.
- Prefer narrow, evidence-backed changes and existing tooling.
- Do not hardcode unverified course sections or enrollment eligibility.
- Keep institution-specific examples and facts traceable to supplied materials; do not treat examples as universal rules.

## Validation

Run the Skill Creator validator against the repository directory. Review Markdown/frontmatter, reference links, Git diff, privacy scan, and redacted course-data examples. Run only tests or examples that actually exist.

## Forbidden

- Do not commit secrets, private paths, personal data, cookies, tokens, or private conversation text.
- Do not delete files whose purpose is unknown.
- Do not hide exceptions or lower validation standards.
- Do not force-push, rewrite public history, or delete a remote repository/branch without explicit authorization.
