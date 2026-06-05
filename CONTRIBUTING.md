# Contributing to SapiSehat

Thank you for your interest in contributing to SapiSehat! This document outlines the process for contributing to the project.

## Code of Conduct

- Be respectful and constructive in all communications
- Focus on the technical merits of contributions
- Help maintain a welcoming environment for all contributors

## Development Workflow

### Branching Strategy

```
main          ← production-ready code only
dev           ← integration branch
feat/xxx      ← new features (from dev)
fix/xxx       ← bug fixes (from dev)
docs/xxx      ← documentation changes
refactor/xxx  ← code refactoring
```

### Getting Started

1. **Fork & Clone**
   ```bash
   git clone <repo-url>
   cd sapisehat
   git checkout dev
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Set Up Development Environment**

   **Backend (Docker):**
   ```bash
   pnpm backend:up
   ```

   **Mobile:**
   Connect device via USB or WiFi (see [Wireless Debugging](docs/Mobile/WIRELESS-DEBUGGING.md)), then:
   ```bash
   pnpm mobile:run
   ```

### Making Changes

1. Write clear, concise commit messages
2. Follow existing code style and patterns
3. Add tests for new functionality
4. Update documentation as needed
5. Keep changes focused and atomic

### Commit Message Format

```
<type>: <short description>

<optional body>
```

**Types:**
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation changes
- `refactor:` — code restructuring
- `test:` — test additions/changes
- `chore:` — maintenance tasks
- `ci:` — CI/CD changes

**Examples:**
```
feat: add image validation endpoint
fix: resolve model loading race condition
docs: update API response format in README
```

### Before Submitting

1. **Run Tests**
   ```bash
   # Backend
   pnpm backend:test

   # Mobile
   pnpm mobile:test
   ```

2. **Check Code Quality**
   - Ensure no linting errors
   - Verify all tests pass
   - Test your changes manually

3. **Update Documentation**
   - Update README if you changed setup/usage
   - Update API docs if endpoints changed
   - Add changelog entry

### Pull Request Process

1. Push your branch and create a PR against `dev`
2. Fill out the PR template completely
3. Ensure CI checks pass
4. Request review from a team member
5. Address review feedback
6. Once approved, merge to `dev`
7. After testing, `dev` is merged to `main` for release

### Architecture Guidelines

**Backend (FastAPI + TensorFlow):**
- **HTTP Layer** (`api/routes.py`): Thin wrapper — no business logic
- **Inference Layer** (`inference_server.py`): Pure logic, no HTTP coupling
- **Model Layer** (`model/loader.py`): Singleton for memory efficiency
- **Preprocessing** (`preprocessing/`): Stateless pure functions

**Key Principle:** Inference logic must remain decoupled from HTTP. This enables future migration (e.g., Go gateway) without rewriting core logic.

**Mobile (Kotlin + Jetpack Compose):**
- MVVM architecture with Hilt DI
- Room for local persistence
- Retrofit for API communication
- TFLite for offline inference fallback

### Testing Guidelines

- New features must include tests
- Bug fixes should include regression tests
- Aim for meaningful coverage, not just metrics
- Test edge cases and error conditions

### Documentation

- Use clear, concise language
- Include code examples where helpful
- Keep README and API docs up to date
- Follow existing documentation structure

## Questions?

Create an issue or contact the maintainers:
- Raditya Rafif Pratama Sasmita
- Noval Putra Ramadhan

Teknik Informatika, Politeknik Negeri Semarang
