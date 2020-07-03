# readthedocs-custom-steps

A hack to run custom steps when building documentation on Read the Docs. 

__Configuration__

```yml
# .readthedocs.yml
version: 2
mkdocs: {}  # tell readthedocs to use mkdocs
python:
  version: 3.7
  install:
    - requirements: requirements.txt  # must contain "readthedocs-custom-steps"
```

```yml
# .readthedocs-custom-steps.yml
steps:
- echo "Custom steps to produce HTML in $SITE_DIR here ..."
```

> __Important__: This module should not be installed outside of a Read the Docs build environment.
> It will rename your Python executable and install a substitute. It does not currently provide an
> automated way to revert this change.

__Testing this package__

To test this package in a similar environment as Read the Docs itself, you can run `make test`.
Note that this requires Docker and a Docker volume called `pip-caches`. Note that the Make command
is expected to return status code `27` as defined in the `test/.readthedocs-custom-steps.yml` file.

__Release process__

Requires [Shore](https://pypi.org/project/nr.shore).

    $ make bump TYPE=--minor
    $ make publish

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
