# Commit Message Examples

Comprehensive examples of conventional commit messages for different scenarios.

## Table of Contents

- [Feature Commits](#feature-commits)
- [Bug Fix Commits](#bug-fix-commits)
- [Documentation Commits](#documentation-commits)
- [Refactoring Commits](#refactoring-commits)
- [Test Commits](#test-commits)
- [Build & CI Commits](#build--ci-commits)
- [Breaking Changes](#breaking-changes)
- [Multi-Change Commits](#multi-change-commits)

---

## Feature Commits

### Simple Feature
```
feat(api): add health check endpoint

Add /health endpoint for monitoring service status.
```

### Feature with Details
```
feat(tasks): implement task priority levels

Add priority field to tasks with three levels: high, medium, low.
Users can set priority when creating tasks and filter by priority
when retrieving tasks.

Changes include:
- Add priority enum to Task model
- Update create/update endpoints to accept priority
- Add priority filter to list endpoint
- Update API documentation with priority examples

Closes #45
```

### Feature with Breaking Change
```
feat(api)!: change authentication to JWT

BREAKING CHANGE: Replace session-based auth with JWT tokens.

All API endpoints now require JWT token in Authorization header
instead of session cookies. Clients must update to use:
Authorization: Bearer <token>

Migration guide:
1. Update client code to use JWT tokens
2. Remove session cookie handling
3. Implement token refresh logic

Closes #67
```

### Feature with Multiple Scopes
```
feat(api,db): add task categories

Implement task categorization feature across API and database layers.
Users can organize tasks into custom categories.

Database changes:
- Add categories table
- Add task_category_id foreign key to tasks

API changes:
- POST /categories - Create category
- GET /categories - List categories
- PUT /tasks/:id - Update task category

Closes #89
```

---

## Bug Fix Commits

### Simple Bug Fix
```
fix(api): correct status code for task not found

Return 404 instead of 500 when task ID doesn't exist.
```

### Bug Fix with Details
```
fix(auth): resolve token expiration race condition

Fix race condition where concurrent requests with expiring tokens
could cause authentication failures. Implement atomic token refresh
with database locking.

The issue occurred when multiple requests arrived simultaneously
with tokens about to expire, causing them to interfere with each
other's refresh attempts.

Fixes #123
```

### Critical Bug Fix
```
fix(db): prevent SQL injection in task search

SECURITY: Sanitize user input in task search to prevent SQL injection.

Affected endpoints:
- GET /tasks?search=<query>
- GET /tasks/search

All user input is now properly escaped using parameterized queries.

Fixes #156
```

### Bug Fix with Workaround
```
fix(api): handle empty request body gracefully

Previously returned 500 error when request body was empty.
Now returns 400 Bad Request with clear error message.

Temporary workaround for issue #178 until we implement request
validation middleware.

Fixes #178
```

---

## Documentation Commits

### README Update
```
docs: add installation instructions for Windows

Include Windows-specific setup steps and common troubleshooting
for uv installation issues.
```

### API Documentation
```
docs(api): update endpoint examples with new parameters

Add examples for recently added query parameters:
- status_filter
- priority_filter
- created_after

All examples now use realistic data and include expected responses.
```

### Code Comments
```
docs(tasks): add docstrings to task service methods

Document all public methods in TaskService class with parameter
descriptions, return types, and usage examples.
```

### Changelog
```
docs: prepare changelog for v2.0.0 release

Summarize all features, bug fixes, and breaking changes since v1.5.0.
Organize changes by category and provide migration guide.
```

---

## Refactoring Commits

### Code Structure
```
refactor(api): extract validation to separate module

Move Pydantic model validation logic from endpoints to dedicated
validators module for better code organization and reusability.

No functional changes.
```

### Simplification
```
refactor(db): simplify query builder

Replace complex query construction with SQLModel's declarative
syntax. Reduces code by 40 lines while maintaining same functionality.

Performance remains identical.
```

### Extraction
```
refactor(tasks): extract task filtering to service layer

Move filtering logic from API endpoints to TaskService to support
reuse across multiple endpoints and improve testability.

Updated affected tests accordingly.
```

### Rename
```
refactor: rename TaskStatus to TaskState

Rename for consistency with domain terminology. Update all references
across codebase including tests and documentation.

This is a pure rename with no logic changes.
```

---

## Test Commits

### New Tests
```
test(api): add integration tests for task CRUD

Add comprehensive integration tests covering:
- Create task with valid/invalid data
- List tasks with filtering
- Update task status
- Delete task

Coverage increased from 85% to 96%.
```

### Fix Flaky Test
```
test(auth): fix intermittent token refresh test failure

Replace time-based assertions with explicit mocking to eliminate
timing issues in token expiration tests.

Fixes #201
```

### Test Refactoring
```
test: extract common fixtures to conftest

Move shared test fixtures (test_db, test_client, sample_task) to
conftest.py to reduce duplication across test files.
```

### Performance Test
```
test(perf): add load testing for task listing

Add locust-based load tests to verify API can handle 1000 concurrent
requests. Current baseline: 500ms p95 latency at 1000 req/s.
```

---

## Build & CI Commits

### Dependency Update
```
build: upgrade FastAPI to v0.104.0

Update FastAPI and related dependencies to latest stable versions.
Includes security fixes and performance improvements.

All tests passing with new versions.
```

### CI Configuration
```
ci: add automated security scanning

Add Bandit security scanning to GitHub Actions workflow.
Runs on every PR to catch potential security issues early.
```

### Build Script
```
build: add Docker build caching

Implement multi-stage Docker build with layer caching to reduce
build time from 5min to 2min in CI pipeline.
```

### Development Tools
```
chore: add pre-commit hooks for code quality

Configure pre-commit hooks for:
- Black formatting
- Ruff linting
- Import sorting with isort
- Trailing whitespace removal

Ensures code quality before commits.
```

---

## Breaking Changes

### API Change
```
feat(api)!: standardize error response format

BREAKING CHANGE: All error responses now use consistent format.

Old format:
{
  "error": "Task not found"
}

New format:
{
  "detail": "Task not found",
  "error_code": "TASK_NOT_FOUND",
  "status": 404
}

Update client code to parse new error format.

Closes #234
```

### Database Schema
```
feat(db)!: change task due_date to datetime

BREAKING CHANGE: due_date field changed from date to datetime
to support time-specific deadlines.

Migration required:
uv run alembic upgrade head

Existing due_date values will be set to 00:00:00 UTC.

Closes #256
```

### Configuration
```
feat(config)!: switch to environment-based configuration

BREAKING CHANGE: Replace config.py with environment variables.

Old: Settings loaded from config.py
New: Settings loaded from .env file

Migration:
1. Copy .env.example to .env
2. Set all required environment variables
3. Remove config.py from imports

Closes #278
```

---

## Multi-Change Commits

### Feature Bundle
```
feat(api): implement complete task management

Add full CRUD functionality for tasks:
- POST /tasks - Create new task
- GET /tasks - List all tasks
- GET /tasks/:id - Get single task
- PUT /tasks/:id - Update task
- DELETE /tasks/:id - Delete task

Includes:
- SQLModel models and schemas
- Full test coverage (26 tests)
- API documentation
- Database migrations

Closes #12, #13, #14, #15, #16
```

### Multiple Bug Fixes
```
fix: resolve critical production issues

Fix multiple issues discovered in production:
- Auth: Fix token refresh race condition (#301)
- DB: Add connection pool timeout handling (#302)
- API: Correct pagination offset calculation (#303)

All issues verified in staging environment before deployment.
```

---

## Special Cases

### Revert Commit
```
revert: revert "feat(api): add task sharing"

This reverts commit abc123def456.

Reverting due to performance issues with large task lists.
Will reimplement with better query optimization.

See #345 for details.
```

### Merge Commit
```
Merge pull request #123 from user/feature-branch

feat(api): add task categories
```

### Initial Commit
```
chore: initial commit

Set up FastAPI project structure with:
- FastAPI application
- SQLModel for database
- pytest for testing
- Docker configuration
- Basic documentation
```

### Hotfix
```
fix(critical): patch authentication bypass vulnerability

SECURITY: Fix critical authentication bypass in token validation.
Deployed immediately to production.

CVE-2024-XXXX

Fixes #400
```

---

## Templates

### Feature Template
```
feat(<scope>): <concise description>

<explain what the feature does and why it's needed>

<list key implementation details if complex>

Closes #<issue-number>
```

### Bug Fix Template
```
fix(<scope>): <concise description>

<explain what was wrong and how it's fixed>

<mention any side effects or related issues>

Fixes #<issue-number>
```

### Breaking Change Template
```
<type>(<scope>)!: <concise description>

BREAKING CHANGE: <clear explanation of the breaking change>

<explain the old behavior>

<explain the new behavior>

<provide migration guide>

Closes #<issue-number>
```

---

## Commit Message Checklist

Before committing, verify:
- [ ] Type is appropriate (feat, fix, docs, etc.)
- [ ] Scope is relevant (api, db, auth, etc.)
- [ ] Subject is imperative mood and ≤50 chars
- [ ] Subject doesn't end with period
- [ ] Body explains "why" not "what"
- [ ] Body lines wrap at 72 characters
- [ ] Breaking changes clearly marked
- [ ] Issues referenced in footer
- [ ] Message will be clear to others in 6 months

## Common Mistakes to Avoid

❌ **Too vague:**
```
fix: update code
```

✅ **Specific:**
```
fix(api): correct status code for invalid task ID
```

---

❌ **Wrong tense:**
```
feat(api): added new endpoint
```

✅ **Imperative mood:**
```
feat(api): add health check endpoint
```

---

❌ **Multiple unrelated changes:**
```
feat: add logging and fix bug and update docs
```

✅ **Separate commits:**
```
feat(logging): add structured logging
fix(api): correct validation error
docs: update API examples
```

---

❌ **Subject too long:**
```
feat(api): add the ability to filter tasks by their status and also by priority level
```

✅ **Concise subject:**
```
feat(api): add task filtering by status and priority
```
