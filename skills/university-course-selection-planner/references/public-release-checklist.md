# Public release checklist

Use this checklist only during the release-review phase.

## Content

- [ ] No private conversation text or author-specific context remains.
- [ ] No personal paths, email addresses, phone numbers, account identifiers, or private files remain.
- [ ] No API keys, tokens, passwords, cookies, or credentials appear in files or Git history.
- [ ] Examples use placeholders and safe fixtures.

## Technical

- [ ] `SKILL.md` frontmatter passes the Skill validator.
- [ ] Every linked reference exists and is necessary.
- [ ] Examples and scripts were tested with safe representative inputs.
- [ ] README installation steps match the actual repository.
- [ ] `.gitignore` excludes local and generated material without hiding source files.

## Legal and GitHub

- [ ] Third-party code, prompts, templates, images, and data have been identified.
- [ ] Required attribution and notices are retained.
- [ ] The chosen license is compatible with all included content.
- [ ] Repository owner, name, visibility, remote URL, and push authorization are confirmed.
- [ ] No force-push or history rewrite is planned.
