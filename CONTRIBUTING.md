# Contributing

Thank you for your interest in contributing! Please discuss any major changes you’d like to make via Discussions, Issues, or email before submitting a pull request.

## Development

1. Fork the project

2. Clone your fork

   ```sh
   git clone https://github.com/{your_profile}/ddgs
   cd ddgs
   ```

3. Create a virtual environment and install development requirements:

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # on Windows use `.venv\Scripts\activate`
   pip install .[dev] orjson
   
4. Create your feature branch
   ```sh
   git checkout -b feat/new-feature
   ```
5. Start hacking! Make your changes.
6. Run the test suite
   ```sh
   pytest
   ```
7. Run type checking, formatting, and linting to ensure code quality
   ```sh
   mypy --install-types .
   ruff format
   ruff check
   ```
8. Commit your changes (please follow the [Conventional Commits](https://www.conventionalcommits.org) specification)
   ```sh
   git add .
   git commit -m 'feat: add feature description'`
   ```
9. Push your branch to your fork
   ```sh
   git push origin feat/new-feature`
   ```
10. Open a Pull Request against the upstream repository.
___
Thanks for helping make this project better! ❤️
