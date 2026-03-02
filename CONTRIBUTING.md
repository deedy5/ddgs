# Contributing

Please open a Discussion, Issue, or email the maintainers to talk over any major changes before submitting a pull request.

## IDE configuration

If you use **VSCode**, install recommended extensions (press `F1` → *Show Recommended Extensions*):

- `ms-python.python`
- `ms-python.mypy-type-checker`
- `charliermarsh.ruff`
- `usernamehw.errorlens`
- `fill-labs.dependi`

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
   prek install
   ```
   - Hooks run `ruff` and `mypy` automatically on each commit.
   - To run them manually: `prek`.

3. Create a feature branch:
   ```sh
   git checkout -b feat/new-feature
   ```
4. Implement your changes.
5. Run tests locally:
   ```sh
   pytest
   ```
6. Commit changes (follow Conventional Commits):
   ```sh
   git add .
   git commit -m "feat: add feature description"
   ```
7. Push your branch to your fork
   ```sh
   git push origin feat/new-feature
   ```
8. Open a pull request against the upstream repository and reference any related Discussion/Issue.


## Code style

   - Formatting and linting are enforced with **ruff**.
   - Static typing is checked with **mypy**.

## PR checklist

   - Tests pass: `pytest`
   - prek checks pass: `prek`
   - Commit messages follow Conventional Commits
   - PR references related Issue/Discussion and describes changes
   - Add tests for new behavior where applicable
