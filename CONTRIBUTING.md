# Contributing to YatinVeda

Thank you for your interest in contributing to YatinVeda! We welcome contributions from the community and appreciate your efforts to improve our Vedic Astrology Intelligence Platform.

## Table of Contents
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)
- [Reporting Issues](#reporting-issues)

## Project Structure

Before contributing, familiarize yourself with the project organization:

- **`backend/`** - FastAPI backend with API endpoints, models, and services
- **`frontend/`** - Next.js frontend application
- **`docs/`** - All project documentation (guides and API docs)
- **`samples/`** - Sample code demonstrating API usage
- **`tests/`** - Test files organized by feature
- **`scripts/`** - Utility scripts for development and deployment

For detailed documentation, see [docs/README.md](docs/README.md).

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- Docker and Docker Compose
- Git

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YatinVeda.git
   cd YatinVeda
   ```

3. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

7. Set up the frontend (in a separate terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Development Workflow

### Branch Strategy
- Create feature branches from the `main` branch
- Name your branches descriptively (e.g., `feature/user-authentication`, `bugfix/login-error`)
- Keep your branches up to date with `main`

### Making Changes
1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```

2. Make your changes following the code style guidelines
3. Write or update tests as needed
4. Run the test suite to ensure everything works:
   ```bash
   # Backend tests
   cd backend
   python -m pytest
   
   # Frontend tests (if applicable)
   cd frontend
   npm test
   ```

5. Commit your changes with a descriptive commit message

## Code Style

### Python
- Follow PEP 8 style guide
- Use Black for code formatting
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions and methods focused and small

### JavaScript/TypeScript
- Use ESLint with the project's configuration
- Follow Airbnb JavaScript Style Guide
- Use TypeScript for type safety

### General Guidelines
- Write clear, descriptive variable and function names
- Keep functions and methods focused on a single responsibility
- Comment complex logic appropriately
- Follow the principle of least surprise

## Testing

### Backend Tests
- Write unit tests for new functionality
- Write integration tests for API endpoints
- Aim for high test coverage, especially for critical paths
- Use pytest for testing

Run all backend tests:
```bash
cd backend
python -m pytest
```

Run tests with coverage:
```bash
python -m pytest --cov=.
```

### Frontend Tests
- Write unit tests for components and utilities
- Write integration tests for complex user flows
- Use Jest and React Testing Library

## Documentation

### Contributing to Documentation

Good documentation is crucial for the project's success. When contributing:

1. **Update relevant docs** - If your changes affect functionality, update the corresponding guide in `docs/guides/`
2. **API changes** - Update `docs/api/API_DOCUMENTATION.md` for any API modifications
3. **New features** - Add a new guide or extend existing ones
4. **Sample code** - Add or update samples in `samples/` directory for new features

### Documentation Structure

- `docs/api/` - API endpoint documentation
- `docs/guides/` - Feature-specific guides and setup instructions
- `docs/README.md` - Documentation index
- `samples/` - Working code examples

### Writing Guidelines

- Use clear, concise language
- Include code examples where appropriate
- Add diagrams for complex workflows
- Keep guides up-to-date with code changes
- Test all sample code before committing

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Update documentation as needed
3. Add tests for new functionality
4. Ensure all tests pass
5. Squash commits if necessary to create a clean history
6. Submit your pull request with a clear title and description
7. Link any related issues in the PR description
8. Be responsive to feedback during the review process

### PR Title Format
Use conventional commits format:
```
feat: Add new user authentication flow
fix: Resolve issue with chart rendering
docs: Update API documentation
style: Format code according to style guide
refactor: Simplify user profile component
test: Add tests for payment processing
chore: Update dependencies
```

### PR Description Template
Include the following in your PR description:
- Summary of changes
- Motivation for changes
- How to test the changes
- Screenshots (if UI changes)
- Breaking changes (if any)
- Related issues

## Commit Messages

Follow the conventional commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(auth): add two-factor authentication`
- `fix(api): resolve timeout issue in chart generation`
- `docs: update installation instructions`
- `refactor: improve user service architecture`

Common types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semi-colons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Other changes that don't modify src or test files

## Reporting Issues

### Before Creating an Issue
- Search existing issues to avoid duplicates
- Check if the issue has been addressed in recent commits
- Ensure you're using the latest version

### Creating Good Issues
- Use a clear, descriptive title
- Provide detailed steps to reproduce the issue
- Include your environment information (OS, Python version, etc.)
- Add screenshots or logs if relevant
- Explain the expected behavior vs. actual behavior

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Questions?

If you have questions about contributing, feel free to open an issue or contact the maintainers.

---

Thank you for contributing to YatinVeda! 🌌