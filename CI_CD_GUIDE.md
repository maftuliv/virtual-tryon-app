# CI/CD Pipeline Guide

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment. The pipeline automatically runs code quality checks, security scans, and tests on every push and pull request.

## Pipeline Components

### 1. Code Quality Checks (`lint-and-type-check`)

Runs multiple code quality tools:
- **Black**: Ensures consistent code formatting
- **isort**: Checks import statement ordering
- **flake8**: Lints for Python syntax errors and code style
- **mypy**: Performs static type checking
- **pylint**: Advanced code quality analysis

### 2. Security Scanning (`security-scan`)

Security vulnerability detection:
- **Safety**: Scans dependencies for known security vulnerabilities
- **Bandit**: Analyzes code for common security issues

### 3. Configuration Validation (`validate-config`)

Validates application configuration:
- Pydantic schema validation
- Environment variable checking
- `.env.example` file validation

### 4. Tests (`test`)

Runs test suite with PostgreSQL service:
- Unit tests with pytest
- Integration tests
- Code coverage reporting

### 5. Build Verification (`build-check`)

Verifies the application builds correctly:
- Python syntax checking
- Import verification for all modules

## Local Development Setup

### Install Development Dependencies

```bash
# Install all development tools
pip install -r requirements-dev.txt
```

### Set Up Pre-commit Hooks

Pre-commit hooks run checks automatically before each commit:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

### Manual Code Quality Checks

Run these commands locally before pushing:

```bash
# Format code with Black
black backend/

# Sort imports
isort backend/

# Lint with flake8
flake8 backend/

# Type check with mypy
mypy backend/ --ignore-missing-imports

# Security scan
bandit -r backend/

# Run tests
pytest tests/ --cov=backend
```

## Configuration Files

### `.flake8`
Flake8 linter configuration:
- Max line length: 120
- Max complexity: 15
- Excludes common directories

### `pyproject.toml`
Centralized configuration for:
- Black (formatter)
- isort (import sorter)
- mypy (type checker)
- pylint (linter)
- pytest (testing)
- coverage (code coverage)

### `.pre-commit-config.yaml`
Pre-commit hooks configuration:
- File checks (trailing whitespace, large files, etc.)
- Code formatting (Black, isort)
- Linting (flake8)
- Security (Bandit)

## GitHub Actions Workflow

### Triggers

The CI pipeline runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### Required Secrets

Add these secrets in GitHub repository settings:

- `JWT_SECRET_KEY`: JWT secret for testing (optional, fallback provided)

### Workflow File

Located at: `.github/workflows/ci.yml`

## Best Practices

### Before Committing

1. Run pre-commit hooks: `pre-commit run --all-files`
2. Run tests locally: `pytest tests/`
3. Check type hints: `mypy backend/`

### Code Standards

- **Line length**: Maximum 120 characters
- **Type hints**: Add type hints to all functions in critical modules
- **Docstrings**: Include docstrings for public functions and classes
- **Imports**: Keep imports organized (stdlib → third-party → local)

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(auth): add type hints to AuthManager methods
fix(config): correct Pydantic validation for database_url
docs(ci): add CI/CD pipeline documentation
```

## Troubleshooting

### Pre-commit Hook Failures

If pre-commit hooks fail:

```bash
# Auto-fix formatting issues
black backend/
isort backend/

# Re-run the commit
git add .
git commit -m "your message"
```

### CI Pipeline Failures

1. Check the GitHub Actions tab in your repository
2. Review failed job logs
3. Fix issues locally and push again

### Type Checking Errors

mypy errors are currently set to `continue-on-error: true` to allow gradual typing adoption. To fix:

1. Add type hints to flagged functions
2. Use `# type: ignore` for unavoidable issues (sparingly)

## Next Steps

### 1. Add Tests

Create `tests/` directory with pytest tests:

```bash
mkdir tests
touch tests/__init__.py
touch tests/test_auth.py
touch tests/test_config.py
```

### 2. Increase Type Coverage

Continue adding type hints to:
- Route handlers in `backend/app.py`
- Helper functions throughout the codebase

### 3. Code Coverage Goals

Aim for:
- 80%+ overall code coverage
- 90%+ for critical authentication and security code

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)
