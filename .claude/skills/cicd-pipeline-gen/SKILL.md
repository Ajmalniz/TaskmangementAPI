---
name: cicd-pipeline-gen
description: Generate CI/CD pipeline configurations for GitHub Actions, GitLab CI, and other platforms. Creates workflows for testing, linting, building, and deploying Python FastAPI applications. Use when the user wants to set up automated testing, implement continuous integration, automate deployments, or asks about CI/CD setup for their project.
---

# CI/CD Pipeline Generator

Generate production-ready CI/CD pipeline configurations for automated testing, building, and deployment.

## What This Skill Does

This skill automatically generates CI/CD pipeline configurations that include:
- Automated testing with pytest
- Code quality checks (linting, formatting)
- Docker image building and pushing
- Deployment automation
- Dependency caching for faster builds
- Multi-environment support (dev, staging, production)
- Security scanning
- Coverage reporting

## Supported Platforms

- **GitHub Actions** (most common)
- **GitLab CI**
- **CircleCI**
- **Jenkins**
- **Azure Pipelines**

## When to Use

Use this skill when the user:
- Wants to set up automated testing for their project
- Needs CI/CD pipeline configuration
- Asks about automating deployments
- Wants to implement continuous integration
- Needs to run tests on every commit/PR
- Wants to automate Docker builds and deployments

## How to Use

### Step 1: Gather Requirements

Ask the user (if not already specified):
1. **Platform**: GitHub Actions, GitLab CI, or other?
2. **Testing**: Run pytest? Include coverage reporting?
3. **Linting**: Include code quality checks (ruff, black, mypy)?
4. **Deployment**: Automatic deployment? To where (Railway, Render, AWS, etc.)?
5. **Triggers**: On push, PR, or both? Specific branches?
6. **Environment**: Single environment or multiple (dev/staging/prod)?

### Step 2: Analyze Project Structure

Check the current project for:
- Testing framework (pytest, unittest)
- Linting tools (from `pyproject.toml` or dev dependencies)
- Docker configuration (Dockerfile present?)
- Python version
- Dependencies management (uv, pip, poetry)

### Step 3: Generate Pipeline Configuration

Based on platform, create appropriate configuration files.

For complete templates, see `references/pipeline-templates.md`.

#### GitHub Actions Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync

    - name: Run tests
      run: uv run pytest --cov --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Run ruff
      run: |
        pip install ruff
        ruff check .

  deploy:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production
      run: |
        # Deployment commands here
        echo "Deploying to production"
```

Customize based on:
- Python version from project
- Package manager (uv, pip, poetry)
- Deployment platform
- Required secrets and environment variables

### Step 4: Add Supporting Files

#### 1. Add Test Coverage Badge

Update `README.md` with status badges:

```markdown
[![CI/CD](https://github.com/username/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/username/repo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/username/repo/badge.svg)](https://codecov.io/gh/username/repo)
```

#### 2. Create Deployment Scripts

If deploying to specific platforms, create deployment scripts in `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Build Docker image
docker build -t myapp:latest .

# Push to registry
docker push myapp:latest

# Deploy (platform-specific)
echo "Deployment complete!"
```

#### 3. Environment Secrets Setup

Document required secrets in `.github/workflows/README.md` or similar:

```markdown
# Required Secrets

Configure these secrets in your repository settings:

- `DATABASE_URL` - Production database connection string
- `DEPLOY_TOKEN` - Deployment platform API token
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
```

### Step 5: Provide Setup Instructions

After generating files, provide clear instructions:

1. **Commit the workflow file:**
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "Add CI/CD pipeline"
   git push
   ```

2. **Configure secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add required secrets (listed in documentation)

3. **Verify workflow:**
   - Check the Actions tab in your repository
   - Ensure the workflow runs successfully
   - Fix any errors in the workflow

4. **Enable branch protection (optional):**
   - Require status checks to pass before merging
   - Require PR reviews
   - Enable automatic deployments on main branch

## Pipeline Best Practices

When generating pipelines, include:

### Testing Stage
- Run all tests with pytest
- Generate coverage reports
- Upload coverage to Codecov or similar
- Cache dependencies for faster builds

### Code Quality Stage
- Run linters (ruff, flake8)
- Run formatters (black, isort)
- Run type checking (mypy)
- Check for security issues (bandit, safety)

### Build Stage
- Build Docker images
- Tag with commit SHA and branch name
- Push to container registry
- Scan images for vulnerabilities

### Deployment Stage
- Deploy only on specific branches (main, production)
- Use different configurations per environment
- Run smoke tests after deployment
- Rollback on failure

## Platform-Specific Features

### GitHub Actions
- Use actions from marketplace (setup-python, codecov, etc.)
- Use matrix builds for multiple Python versions
- Use environments for deployment protection
- Enable dependabot for automatic dependency updates

### GitLab CI
- Use GitLab CI/CD templates
- Enable Auto DevOps if applicable
- Use Review Apps for PR previews
- Configure GitLab Container Registry

### CircleCI
- Use CircleCI orbs for common tasks
- Configure workspace persistence
- Use CircleCI context for secrets
- Enable test splitting for parallel execution

## Common Pipeline Patterns

See `references/pipeline-templates.md` for complete examples of:
- **Basic Test Pipeline**: Run tests on every push
- **Full CI/CD Pipeline**: Test, lint, build, deploy
- **Multi-Environment Pipeline**: Dev, staging, production
- **Monorepo Pipeline**: Multiple services in one repo
- **Matrix Testing Pipeline**: Test across Python versions

## Troubleshooting

Common issues to address:

1. **Dependency caching**: Use platform-specific caching to speed up builds
2. **Environment variables**: Use secrets for sensitive data
3. **Permissions**: Ensure workflow has necessary permissions
4. **Rate limits**: Be mindful of API rate limits in tests
5. **Flaky tests**: Implement retry logic or fix non-deterministic tests

## Output Format

Always create configuration files in this order:
1. Main pipeline configuration (`.github/workflows/ci.yml` or equivalent)
2. Deployment scripts (if needed)
3. Documentation for required secrets
4. Update README with status badges
5. Provide setup instructions

Confirm platform choice and requirements with user before generating files.
