# Building the Worker Placement distribution

For the complete install and usage guide, read [officekit/README.md](../officekit/README.md). Install from source; this repository does not assume a published PyPI package.

From the repository root, with your virtual environment active:

```sh
python3 officekit_dist/assemble.py --no-wheel
python3 -m pip install './officekit_dist/build[ai]'
wp init --dir ../my-office
wp serve --dir ../my-office
```

`assemble.py` stages only the portable OfficeKit packages and selected strategy packs. It excludes the private desk, research datasets and agent handoff. Public page assets and usage documentation are packaged with the engine. Running without `--no-wheel` also builds a wheel.

Extras: `ai` installs the OpenAI and Anthropic clients; `ibkr` remains a compatibility extra. IBKR, Robinhood and TOTP clients are included in the base distribution. Install extras against the assembled path, for example `python3 -m pip install './officekit_dist/build[ai,ibkr]'`.

The monorepo root's `pyproject.toml` describes the SignalOS research framework, not Worker Placement. Do not use `pip install .` there to install the product.

## Package verification

```sh
python3 -m pytest -q tests/test_officekit_portable.py
```

This builds and installs a wheel into an isolated directory, then builds an independent synthetic household. It checks package data and missing-capability reporting without broker or model calls. Real broker compatibility requires separate integration checks.

Code is Apache-2.0; source data permissions are separate in `DATA_LICENSE.md`.
Reproducible dependencies: `python -m pip install --require-hashes -r officekit_dist/requirements.lock`.
Then install the assembled package with `--no-deps --no-build-isolation`.
