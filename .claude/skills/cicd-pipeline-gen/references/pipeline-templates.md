# CI/CD Pipeline Templates

Complete pipeline configurations for different platforms and use cases.

## Table of Contents

- [GitHub Actions Templates](#github-actions-templates)
  - [Basic Test Pipeline](#basic-test-pipeline)
  - [Full CI/CD Pipeline](#full-cicd-pipeline)
  - [Multi-Environment Pipeline](#multi-environment-pipeline)
  - [Matrix Testing](#matrix-testing)
- [GitLab CI Templates](#gitlab-ci-templates)
- [Platform Deployment Examples](#platform-deployment-examples)

---

## GitHub Actions Templates

### Basic Test Pipeline

Simple pipeline that runs tests on every push and pull request.

**.github/workflows/test.yml:**

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-uv-

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync

    - name: Run tests
      run: uv run pytest -v

    - name: Generate coverage report
      run: uv run pytest --cov=. --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

### Full CI/CD Pipeline

Comprehensive pipeline with testing, linting, building, and deployment.

**.github/workflows/ci-cd.yml:**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    name: Code Quality Checks
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Install linting tools
      run: |
        pip install ruff black isort mypy

    - name: Run ruff
      run: ruff check .

    - name: Check formatting with black
      run: black --check .

    - name: Check import sorting
      run: isort --check-only .

    - name: Type checking with mypy
      run: mypy . --ignore-missing-imports
      continue-on-error: true

  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync

    - name: Run tests with coverage
      run: uv run pytest --cov=. --cov-report=xml --cov-report=html -v

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

    - name: Archive coverage results
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/

  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Install security tools
      run: pip install bandit safety

    - name: Run bandit security scan
      run: bandit -r . -f json -o bandit-report.json
      continue-on-error: true

    - name: Check dependencies for vulnerabilities
      run: safety check --json
      continue-on-error: true

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ secrets.DOCKER_USERNAME }}/myapp
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.myapp.com

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add deployment commands here

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://myapp.com

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Add deployment commands here

    - name: Run smoke tests
      run: |
        echo "Running smoke tests"
        # Add smoke test commands
```

---

### Multi-Environment Pipeline

Deploy to different environments based on branch.

**.github/workflows/deploy.yml:**

```yaml
name: Deploy

on:
  push:
    branches:
      - main
      - staging
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set environment variables
      id: set-env
      run: |
        if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          echo "ENVIRONMENT=production" >> $GITHUB_OUTPUT
          echo "URL=https://api.production.com" >> $GITHUB_OUTPUT
        elif [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
          echo "ENVIRONMENT=staging" >> $GITHUB_OUTPUT
          echo "URL=https://api.staging.com" >> $GITHUB_OUTPUT
        else
          echo "ENVIRONMENT=development" >> $GITHUB_OUTPUT
          echo "URL=https://api.dev.com" >> $GITHUB_OUTPUT
        fi

    - name: Deploy to ${{ steps.set-env.outputs.ENVIRONMENT }}
      env:
        ENVIRONMENT: ${{ steps.set-env.outputs.ENVIRONMENT }}
        DATABASE_URL: ${{ secrets[format('DATABASE_URL_{0}', steps.set-env.outputs.ENVIRONMENT)] }}
      run: |
        echo "Deploying to $ENVIRONMENT"
        echo "API URL: ${{ steps.set-env.outputs.URL }}"
        # Deployment commands here

    - name: Health check
      run: |
        sleep 10
        curl -f ${{ steps.set-env.outputs.URL }}/health || exit 1
```

---

### Matrix Testing

Test across multiple Python versions.

**.github/workflows/matrix-test.yml:**

```yaml
name: Matrix Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install uv
        uv sync

    - name: Run tests
      run: uv run pytest -v

    - name: Upload results
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{ matrix.os }}-${{ matrix.python-version }}
        path: test-results/
```

---

## GitLab CI Templates

### Basic GitLab CI Pipeline

**.gitlab-ci.yml:**

```yaml
stages:
  - test
  - build
  - deploy

variables:
  PYTHON_VERSION: "3.11"

# Cache dependencies
.cache_template: &cache_template
  cache:
    paths:
      - .venv/
    key:
      files:
        - pyproject.toml

# Test job
test:
  stage: test
  image: python:${PYTHON_VERSION}
  <<: *cache_template
  before_script:
    - pip install uv
    - uv sync
  script:
    - uv run pytest --cov --cov-report=term --cov-report=xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# Lint job
lint:
  stage: test
  image: python:${PYTHON_VERSION}
  before_script:
    - pip install ruff black
  script:
    - ruff check .
    - black --check .

# Build Docker image
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  only:
    - main
    - develop

# Deploy to production
deploy:production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying to production"
    # Add deployment commands
  environment:
    name: production
    url: https://api.production.com
  only:
    - main
```

---

## Platform Deployment Examples

### Deploy to Railway

```yaml
- name: Deploy to Railway
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
  run: |
    npm i -g @railway/cli
    railway up --service ${{ secrets.RAILWAY_SERVICE_ID }}
```

### Deploy to Render

```yaml
- name: Deploy to Render
  env:
    RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
  run: |
    curl -X POST \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      "https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys"
```

### Deploy to Fly.io

```yaml
- name: Deploy to Fly.io
  uses: superfly/flyctl-actions/setup-flyctl@master

- run: flyctl deploy --remote-only
  env:
    FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Deploy to AWS (via Docker)

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1

- name: Login to Amazon ECR
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push to ECR
  run: |
    docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

- name: Deploy to ECS
  run: |
    aws ecs update-service \
      --cluster ${{ secrets.ECS_CLUSTER }} \
      --service ${{ secrets.ECS_SERVICE }} \
      --force-new-deployment
```

---

## Customization Guide

When adapting templates:

1. **Python Version**: Update `PYTHON_VERSION` to match project
2. **Package Manager**: Replace `uv` with `pip` or `poetry` if needed
3. **Test Framework**: Adjust test commands for unittest, nose, etc.
4. **Linting Tools**: Add/remove linters based on project setup
5. **Deployment Platform**: Use appropriate deployment commands
6. **Secrets**: Configure all required secrets in CI/CD settings
7. **Branch Strategy**: Adjust branch names to match workflow
8. **Environments**: Configure environment protection rules

## Required Secrets

Common secrets needed across platforms:

- `DATABASE_URL` or `DATABASE_URL_PRODUCTION`, `DATABASE_URL_STAGING`
- `DOCKER_USERNAME` and `DOCKER_PASSWORD`
- `RAILWAY_TOKEN` (if using Railway)
- `RENDER_API_KEY` (if using Render)
- `FLY_API_TOKEN` (if using Fly.io)
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (if using AWS)
- Custom API keys for deployment platforms
