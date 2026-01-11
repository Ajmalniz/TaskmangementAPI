---
name: git-commit-msg
description: Generate well-formatted, conventional commit messages following best practices and industry standards. Creates semantic commit messages with proper type, scope, and description. Use when the user wants to commit changes, needs help writing commit messages, asks about git commit conventions, or wants to maintain clean git history.
---

# Git Commit Message Builder

Generate conventional, semantic commit messages that follow industry best practices and maintain clean git history.

## What This Skill Does

This skill helps create commit messages that:
- Follow Conventional Commits specification
- Include proper type, scope, and description
- Provide meaningful context for code changes
- Work with automated changelog generation
- Support semantic versioning
- Pass commit message linters

## When to Use

Use this skill when:
- User wants to commit changes and needs a good commit message
- User asks "what should my commit message be?"
- User wants to follow conventional commit standards
- User needs help describing their changes
- User wants to maintain clean git history
- User is working with tools that parse commit messages (semantic-release, changelog generators)

## Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Components

**Type** (required): The kind of change
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, missing semicolons, etc.)
- `refactor` - Code refactoring without changing functionality
- `perf` - Performance improvements
- `test` - Adding or updating tests
- `build` - Build system or dependency changes
- `ci` - CI/CD configuration changes
- `chore` - Other changes that don't modify src or test files
- `revert` - Reverts a previous commit

**Scope** (optional): The area of codebase affected
- `api` - API endpoints
- `auth` - Authentication
- `db` - Database
- `ui` - User interface
- `tests` - Testing
- Custom scopes based on project structure

**Subject** (required): Short description (50 chars or less)
- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- Be specific and concise

**Body** (optional): Detailed explanation
- Explain the "why" not the "what"
- Wrap at 72 characters
- Separate from subject with blank line

**Footer** (optional): Breaking changes and issue references
- `BREAKING CHANGE:` for breaking changes
- `Closes #123` for issue references
- `Co-authored-by:` for multiple authors

## How to Use

### Step 1: Analyze Changes

First, review what changes were made:

```bash
git status
git diff --staged
```

Understand:
- What files were changed?
- What functionality was added/removed/modified?
- Why were these changes made?
- Are there breaking changes?
- Does this close any issues?

### Step 2: Determine Commit Type

Based on the changes, select the appropriate type:

| Change Description | Type |
|-------------------|------|
| Added new API endpoint | `feat` |
| Fixed a bug | `fix` |
| Updated README | `docs` |
| Reformatted code | `style` |
| Reorganized code structure | `refactor` |
| Improved query performance | `perf` |
| Added unit tests | `test` |
| Updated dependencies | `build` |
| Modified CI workflow | `ci` |
| Updated .gitignore | `chore` |

### Step 3: Identify Scope

Determine which part of the codebase is affected:

- For API changes: `api`
- For database changes: `db`
- For authentication: `auth`
- For tests: `tests`
- For UI components: `ui`
- For specific features: use feature name

### Step 4: Write Subject Line

Create a concise subject (max 50 characters):

**Good examples:**
- `feat(api): add task filtering by status`
- `fix(auth): resolve token expiration issue`
- `docs: update installation instructions`
- `test(api): add integration tests for CRUD`
- `refactor(db): simplify query builder`

**Bad examples:**
- `Added new feature` (too vague, wrong tense)
- `Fix bug` (not specific enough)
- `Updated the authentication system to fix token issues` (too long)

### Step 5: Add Body (if needed)

Include body when:
- Change is complex and needs explanation
- Need to explain the "why" behind the change
- There are multiple related changes
- Need to provide context for future developers

Format:
```
feat(api): add task filtering by status

Users can now filter tasks by status (pending, in_progress, completed)
using the query parameter ?status_filter=<status>. This addresses the
most requested feature from user feedback.

The implementation uses SQLModel's filtering capabilities and maintains
backward compatibility with existing API clients.
```

### Step 6: Add Footer (if needed)

Include footer for:
- Breaking changes
- Issue references
- Multiple authors

Examples:
```
BREAKING CHANGE: API endpoint /tasks now requires authentication

Closes #123
Closes #456

Co-authored-by: Jane Doe <jane@example.com>
```

## Complete Examples

See `references/commit-examples.md` for comprehensive examples of different commit types and scenarios.

### Example 1: New Feature

```
feat(api): add task priority levels

Implement priority levels (high, medium, low) for tasks. Users can now
set and filter tasks by priority through the API.

Changes include:
- Add priority field to Task model
- Update API endpoints to support priority
- Add database migration for priority column
- Include priority in API documentation

Closes #45
```

### Example 2: Bug Fix

```
fix(auth): prevent token refresh race condition

Resolve race condition that occurred when multiple requests attempted
to refresh the same expired token simultaneously. Now using atomic
operations with database locks.

This fixes intermittent 401 errors reported by users.

Fixes #78
```

### Example 3: Documentation Update

```
docs: add API usage examples to README

Include code examples for all CRUD operations using both curl and
Python requests library. This should help new users get started
more quickly.
```

### Example 4: Refactoring

```
refactor(db): extract database session management

Move session management logic to database.py for better separation
of concerns. This makes it easier to test and maintain database
connection handling.

No functional changes.
```

### Example 5: Breaking Change

```
feat(api): change task status enum values

BREAKING CHANGE: Task status values changed from integers (0,1,2)
to strings ("pending", "in_progress", "completed") for better
API clarity and maintainability.

Migration guide:
- Update client code to use string values
- Run database migration to convert existing data
- Update API documentation references

Closes #92
```

## Best Practices

### Do's
- ✅ Use present tense imperative mood ("add" not "added")
- ✅ Keep subject line under 50 characters
- ✅ Separate subject from body with blank line
- ✅ Wrap body at 72 characters
- ✅ Explain "why" in the body, not "what" (code shows "what")
- ✅ Reference issues and PRs in footer
- ✅ Use conventional commit types
- ✅ Be specific and descriptive

### Don'ts
- ❌ Don't use past tense ("added", "fixed")
- ❌ Don't end subject with period
- ❌ Don't capitalize first letter of subject
- ❌ Don't be vague ("update code", "fix stuff")
- ❌ Don't commit multiple unrelated changes together
- ❌ Don't include file names (git knows this)
- ❌ Don't use "and" in subject (split into multiple commits)

## Workflow Integration

### Standard Workflow

```bash
# 1. Stage changes
git add .

# 2. Review changes
git diff --staged

# 3. Generate commit message (using this skill)
# Claude will analyze changes and suggest message

# 4. Commit with generated message
git commit -m "feat(api): add task filtering by status"

# 5. Push changes
git push
```

### With Commit Message Template

Create `.gitmessage` template:

```
<type>(<scope>): <subject>

# Why was this change made?


# What are the key changes?


# Are there any breaking changes?


# Related issues:
# Closes #
```

Configure git to use template:
```bash
git config --global commit.template ~/.gitmessage
```

### Commit Message Linting

For projects using commitlint, the messages generated by this skill will pass validation:

```json
{
  "extends": ["@commitlint/config-conventional"]
}
```

## Commit Message for AI-Assisted Development

When committing code created with AI assistance (like Claude Code), optionally include:

```
feat(api): add user authentication endpoints

Implement JWT-based authentication with login and logout endpoints.
Includes token refresh mechanism and proper error handling.

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Quick Reference

For common scenarios and templates, see `references/commit-examples.md`.

**Quick selection guide:**
- New feature → `feat`
- Bug fix → `fix`
- Documentation → `docs`
- Reformatting → `style`
- Code restructure → `refactor`
- Performance → `perf`
- Tests → `test`
- Dependencies → `build`
- CI/CD → `ci`
- Other → `chore`

## Output Format

When generating commit messages:
1. Analyze the staged changes
2. Determine appropriate type and scope
3. Write concise subject line (≤50 chars)
4. Add body if changes are complex (wrapped at 72 chars)
5. Add footer for breaking changes or issue references
6. Provide the complete commit message
7. Show the git command to use

Example output:
```
Here's your commit message:

feat(api): add task filtering by status

Users can now filter tasks using ?status_filter parameter.
Supports pending, in_progress, and completed statuses.

Closes #45

To commit:
git commit -m "feat(api): add task filtering by status

Users can now filter tasks using ?status_filter parameter.
Supports pending, in_progress, and completed statuses.

Closes #45"
```
