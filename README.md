# readthedocs-custom-steps

A hack to run custom steps when building documentation on Read the Docs.

> __Important__: This module should not be installed outside of a Read the Docs build environment.
> It will rename your Python executable and install a substitute. It does not currently provide an
> automated way to revert this change.

## How to use this?

Rtd-cs overrides your `python` installation with a Bash script that dispatches the
execution of custom steps upon invokation of `python -m mkdocs` or `python -m sphinx`.
The commands to run are defined in a file called `.readthedocs-custom-steps.yml`.

__Example:__

```yml
# .readthedocs-custom-steps.yml
steps:
- bash .scripts/generate-changelog.sh >docs/changelog.md
- python -m "$@"
```

Here, `$@` contains the arguments after `python -m` in the Read the Docs build step, for example:

* `mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml`
* `sphinx -T -b html -d _build/doctrees -D language=en . _build/html`

An infinite recursion of this script invoking itself in the example above is prevented automatically
with the `RTD_CUSTOM_ENTRY` environment variable.

## Configuration

The file containing the steps must be a YAML file called `.readthedocs-custom-steps.yml`. It is searched
for in the following locations:

1. `.readthedocs-custom-steps.yml`
2. `docs/.readthedocs-custom-steps.yml`
3. Relative to any directories from which requirements files are specified in the `.readthedocs.yml` file
   under the `$.python.install[*].requirements` configuration option.

## Environment

In addition to passing the original arguments to the custom steps, Rtd-cs provides `PYTHON` environment variables
as detected from the `~/.pyenv/shims` folder in the RTD build environment. (e.g. if there is a shim `python3.6` and
`python3.7`, there'll be `PYTHON`, `PYTHON36` and `PYTHON37` environment variables, and `PYTHON` will point to 3.7).

---

<p align="center">Copyright &copy; 2021 Niklas Rosenstein</p>
