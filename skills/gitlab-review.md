---
name: gitlab-review
description: Review GitLab merge requests using glab CLI. Trigger phrases include 'review MR', 'review !123', 'code review', 'review merge request'.
---

# GitLab Code Review

Perform comprehensive code reviews of GitLab merge requests, providing actionable feedback on code quality, security, performance, and best practices.

## GitLab Instance

- **URL**: https://gitlab.autocore.net.cn/
- **User**: sanmu.he
- **CLI**: `glab` (already configured with access token)
- **Env**: Always set `GLAB_NO_UPDATE_NOTIFIER=1` before running glab commands

## When to Use

Activate this skill when:

- User types "review" or "code review" (with or without slash command)
- User types "review !123" or "review MR 123" to review a specific merge request
- User types "review #456" to review the MR associated with a GitLab issue
- User provides an MR URL like `https://gitlab.autocore.net.cn/group/project/-/merge_requests/123`
- User provides a commit URL like `https://gitlab.autocore.net.cn/group/project/-/commit/<sha>` (auto-find associated MR)
- User asks to review a merge request, analyze code changes before merging, or check for issues

## Critical Rules

- **Always confirm project path** before reviewing merge requests
- **Always provide constructive feedback framed as questions**, not directives
- **Only review changes introduced in the merge request**, not unrelated code

## Workflow

### 1. Identify the Merge Request

**MR IID + project provided** (e.g., "review !42 in group/project" or "review !42 acdev/sys/xxx"):
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab mr view 42 -R group/project
```

**MR URL provided** (e.g., `https://gitlab.autocore.net.cn/acdev/sys/xxx/-/merge_requests/123`):
- Extract project path and MR IID from URL pattern: `/<project_path>/-/merge_requests/<IID>`

**Commit URL provided** (e.g., `https://gitlab.autocore.net.cn/acdev/sys/xxx/-/commit/<sha>`):
- Extract project path and commit SHA from URL
- Find the associated MR via API:
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/repository/commits/<sha>/merge_requests"
```
- Use the first MR found, or if it's a merge commit, extract MR IID from commit message ("See merge request ...!NNN")

**GitLab Issue ID provided** (e.g., "review #456 in group/project"):
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo 'group/project' | sed 's/\//%2F/g')/issues/456/related_merge_requests"
```
If multiple MRs found, ask user to select.

**No MR specified** (e.g., just "review"):
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab mr list -R group/project
```
Present the list and ask user to select.

### 2. Gather MR Context

```bash
# MR details (title, description, branches, status, approvals)
GLAB_NO_UPDATE_NOTIFIER=1 glab mr view <IID> -R <project>

# MR diff (the actual code changes)
GLAB_NO_UPDATE_NOTIFIER=1 glab mr diff <IID> -R <project>
```

Extract key information:
```
Project: group/project
MR: !123 - "Feature: Add user authentication"
Author: @username
Source: feature/auth → Target: main
Status: Open | Pipeline: Passed | Approvals: 1/2
```

### 3. Check Existing Discussions

```bash
# Get existing notes/comments to avoid duplicate feedback
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/merge_requests/<IID>/notes?per_page=100&sort=asc"
```

- Review existing feedback and discussions
- Avoid duplicate comments
- Check for unresolved threads

### 4. Check Pipeline Status

```bash
# Get pipeline status
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/merge_requests/<IID>/pipelines"
```

- Verify CI/CD pipeline status
- If pipeline failed, check job output:
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/pipelines/<pipeline_id>/jobs"
```

### 5. Analyze Changes

**Only review changes introduced in this merge request.**

**Bugs (primary focus)**
- Logic errors, off-by-one mistakes, incorrect conditionals
- Missing guards, unreachable code paths
- Edge cases: null/empty/undefined inputs, error conditions, race conditions
- Broken error handling that swallows failures or throws unexpectedly

**Code Quality**
- Code style and formatting consistency
- Variable and function naming conventions
- DRY (Don't Repeat Yourself) violations
- Proper abstraction levels
- Excessive nesting that could be flattened

**Security**
- Input validation
- Injection vulnerabilities (SQL, XSS, command injection)
- Hardcoded credentials or secrets
- Unsafe operations, data exposure

**Performance (only flag if obviously problematic)**
- O(n²) on unbounded data, N+1 queries
- Blocking I/O on hot paths
- Resource management (memory leaks, connection handling)

**Best Practices**
- Test coverage implications
- Documentation completeness
- API consistency and backward compatibility
- New dependencies added

### 6. Generate Review Report

```markdown
# Code Review: !{IID} - {TITLE}

## Summary
{Brief overview of changes and overall assessment}

## MR Details
- **Project**: {project_path}
- **Author**: @{author}
- **Branch**: {source_branch} → {target_branch}
- **Pipeline**: {status}
- **Approvals**: {current}/{required}

## Stats
| Metric | Count |
|--------|-------|
| Files Changed | {count} |
| Lines Added | +{additions} |
| Lines Removed | -{deletions} |
| Commits | {commit_count} |

## Strengths
- {what was done well}

## Issues

### 🔴 Critical (must fix before merging)
{bugs, security issues, or "None"}

### 🟡 Important (should address)
{performance, maintainability, or "None"}

### 🟢 Suggestions (nice to have)
{improvements, or "None"}

## Security Review
{specific security findings or "No security concerns identified"}

## Performance Review
{performance implications or "No performance concerns identified"}

## Testing Recommendations
- {what tests should be added}

## Documentation Needs
- {what documentation should be updated}

## Verdict
{APPROVED | CHANGES_REQUESTED | NEEDS_DISCUSSION}
```

### 7. Add Comments to MR (Optional)

**CRITICAL: Always ask user before adding comments to the MR.**

**General comment:**
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab mr note <IID> -R <project> -m "Review comment here"
```

**Line-specific comment (via API):**
```bash
# First get diff_refs
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/merge_requests/<IID>" | python3 -c "import sys,json; d=json.load(sys.stdin)['diff_refs']; print(f\"base={d['base_sha']} head={d['head_sha']} start={d['start_sha']}\")"

# Then create a discussion thread on a specific line
GLAB_NO_UPDATE_NOTIFIER=1 glab api "projects/$(echo '<project>' | sed 's/\//%2F/g')/merge_requests/<IID>/discussions" \
  -X POST \
  -f "body=Could this be simplified with an early return?" \
  -f "position[position_type]=text" \
  -f "position[base_sha]=<base_sha>" \
  -f "position[head_sha]=<head_sha>" \
  -f "position[start_sha]=<start_sha>" \
  -f "position[new_path]=<file_path>" \
  -f "position[new_line]=<line_number>"
```

**Approve MR:**
```bash
GLAB_NO_UPDATE_NOTIFIER=1 glab mr approve <IID> -R <project>
```

## Feedback Style: Questions, Not Directives

Frame all feedback as questions. This encourages dialogue and respects the author's context.

**Don't write:**
- "You should use early returns here"
- "This needs error handling"
- "Extract this into a separate function"

**Do write:**
- "Could this be simplified with an early return?"
- "What happens if this API call fails? Would error handling help here?"
- "Would it make sense to extract this into its own function for reusability?"
- "Is there a scenario where this could be null? If so, how should we handle it?"

## Important Rules

1. **Only review changes from THIS merge request** - do not comment on unchanged code
2. **Frame feedback as questions** to encourage dialogue
3. **Be certain** - don't flag something as a bug unless you're confident it is one
4. **Prioritize clearly**: Critical > Important > Suggestions
5. **Acknowledge good practices** - note what was done well
6. **Check pipeline status** before concluding review
7. **Review existing discussions** to avoid duplicate feedback
8. **Ask before adding comments** to the MR
9. **Language**: Determined by flag in user input:
    - `-c` or `--cn`: 中文报告（默认）
    - `-e` or `--en`: English report
    - No flag: 中文报告
    - Language applies to the entire report: section headers, descriptions, issue explanations, verdict
10. **Direct output** - Do NOT show intermediate glab command outputs to user. Gather all info silently, then output the final structured review report directly
