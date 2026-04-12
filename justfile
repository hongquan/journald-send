# Build documentation
docs:
    uv run maturin develop
    uv run sphinx-build -b html docs docs/_build

# Build and serve documentation
docs-serve:
    uv run python -m sphinx_autobuild -b html docs docs/_build --port 8080

# Clean build artifacts
clean:
    rm -rf docs/_build
    cargo clean
