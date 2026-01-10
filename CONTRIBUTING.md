# Contributing to AWS WasteFinder

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/devopsjunctionn/AWS-WasteFinder.git
cd AWS-WasteFinder

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov moto[ec2,elbv2,sagemaker,sts] flake8
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=wasteFinder --cov-report=term-missing

# Run a specific test
pytest tests/test_waste_finder.py::TestAWSWasteFinder::test_scan_ebs_volumes_finds_orphaned_volumes -v
```

## Git Workflow

### Branch Naming

- `feature/*` - New features (e.g., `feature/add-rds-scanning`)
- `bugfix/*` - Bug fixes (e.g., `bugfix/fix-snapshot-age-calc`)
- `docs/*` - Documentation updates (e.g., `docs/update-readme`)
- `refactor/*` - Code refactoring (e.g., `refactor/simplify-report-gen`)

### Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main` using the naming convention above
3. **Make your changes** with clear, atomic commits
4. **Run tests** locally to ensure nothing is broken
5. **Update documentation** if needed
6. **Submit a PR** with a clear description of changes

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add RDS instance scanning
fix: correct snapshot age calculation  
docs: update installation instructions
test: add unit tests for ELB scanning
refactor: simplify cost calculation logic
```

## Code Style

- Follow PEP 8 guidelines
- Maximum line length: 120 characters
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Run `flake8` before submitting PRs

```bash
flake8 wasteFinder.py --max-line-length=120
```

## Adding New Waste Types

To add a new waste type scanner:

1. Add a new method `scan_<service>` in `AWSWasteFinder` class
2. Follow the pattern of existing scan methods
3. Add the service to `scan_region()` method
4. Update pricing constants if needed
5. Add unit tests with moto mocking
6. Update README with the new waste type

## Reporting Issues

When reporting issues, please include:

- Python version (`python --version`)
- AWS CLI version (`aws --version`)
- Operating system
- Full error traceback
- Steps to reproduce

## Questions?

Open an issue or discussion on GitHub!
