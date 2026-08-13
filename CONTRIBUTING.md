# Contributing to NEXORUX ERP

Thank you for your interest in contributing to NEXORUX ERP! This document provides guidelines and best practices for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include steps to reproduce, expected behavior, and actual behavior
4. Include environment details (OS, Python/Node versions, etc.)

### Suggesting Features

1. Check existing issues and discussions
2. Use the feature request template
3. Describe the problem and proposed solution
4. Consider alignment with project scope

### Pull Requests

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request to `develop`

## Development Setup

See [README.md](README.md) for local development setup instructions.

## Code Style Guidelines

### Backend (Python)

- Follow PEP 8
- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for linting
- Write type hints for function signatures
- Write docstrings for public functions/classes
- Use async/await for all I/O operations

### Frontend (TypeScript/React)

- Use TypeScript for all new code
- Follow React best practices (hooks, functional components)
- Use Tailwind CSS for styling
- Write tests for new components
- Use meaningful component and variable names

## Testing

### Backend Tests

```bash
cd backend
.venv311\Scripts\python.exe -m pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
- `feat(auth): add refresh token endpoint`
- `fix(invoice): correct tax calculation for discounts`
- `docs(readme): update deployment instructions`

## Review Process

1. All PRs require at least one review
2. CI/CD must pass (lint, tests, build)
3. Code coverage should not decrease
4. Documentation must be updated for user-facing changes

## Questions?

Feel free to open an issue or reach out to the maintainers.
