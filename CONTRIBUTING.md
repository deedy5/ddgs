# Contributing

Thanks for your interest in contributing! Please open a Discussion, Issue, or email the maintainers to talk over any major changes before submitting a pull request.

## Development

1. Fork the repository and clone your fork:
   ```sh
   git clone https://github.com/{your_profile}/ddgs
   cd ddgs
   ```

2. Create and activate a virtual environment, then install development dependencies:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e .[dev]
   ```

3. Install pre-commit hooks (automates formatting, linting, typing):
   ```sh
   pre-commit install
   ```
   - Hooks run `ruff` and `mypy` on each commit.
   - To run them manually: `pre-commit run --all-files`.

5. Create a feature branch:
   ```sh
   git checkout -b feat/new-feature
   ```
6. Implement your changes.
7. Run tests locally:
   ```sh
   pytest
   ```
8. Commit changes (follow Conventional Commits):
   ```sh
   git add .
   git commit -m "feat: add feature description"
   ```
9. Push your branch to your fork
   ```sh
   git push origin feat/new-feature
   ```
10. Open a pull request against the upstream repository and reference any related Discussion/Issue.


## Code style

   - Formatting and linting are enforced with **ruff**. The rule set and configuration live in pyproject.toml — follow those rules.
   - Static typing is checked with **mypy**. Add/maintain type annotations where appropriate and ensure mypy passes locally.
   - pre-commit runs ruff and mypy automatically on commits; use `pre-commit run --all-files` to check everything before pushing.

## PR checklist (recommended)

   - Tests pass: `pytest`
   - pre-commit checks pass: `pre-commit run --all-files`
   - Commit messages follow Conventional Commits
   - PR references related Issue/Discussion and describes changes
   - Add tests for new behavior where applicable


Thanks for helping improve the project! ❤️
