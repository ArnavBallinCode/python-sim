# Release process

The project is released from version tags. The first release is `v0.1.0`; it is not published automatically by this repository state.

## Local preparation

1. Update `version` in `pyproject.toml`.
2. Add the release date and accurate entries to `CHANGELOG.md`.
3. Run `python3 -m pytest`, `ruff check .`, and `mypy src tests`.
4. Run `python3 -m build` and inspect both `dist/*.whl` and `dist/*.tar.gz`.
5. Install the wheel in a clean virtual environment and run the canonical example.
6. Review the diff and create a pull request.

## TestPyPI validation

Run the **Publish to TestPyPI** workflow manually from GitHub Actions. Install the uploaded candidate into a fresh environment using:

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ python-sim==VERSION
```

Run the example and smoke tests before production release.

## Production release

1. Merge the release changes to `main`.
2. Create and push an annotated tag such as `v0.1.0`.
3. The `Publish release` workflow builds the wheel and sdist, publishes them to PyPI with OIDC Trusted Publishing, and creates a GitHub Release with both files and the changelog.

The workflow does not contain PyPI passwords or API tokens.

## One-time Trusted Publishing setup

Create the `pypi` and `testpypi` GitHub environments. On each corresponding package index, add a pending trusted publisher with:

- owner: `ArnavBallinCode`
- repository: `python-sim`
- workflow file: `publish.yml` for PyPI, `publish-testpypi.yml` for TestPyPI
- environment: `pypi` for PyPI, `testpypi` for TestPyPI

On GitHub, enable Pages using **GitHub Actions** as the source. The docs workflow uses the supported Pages artifact and deployment actions. Add environment protection rules or required reviewers before production publishing if the project needs a manual approval gate.
