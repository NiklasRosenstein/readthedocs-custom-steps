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
    - requirements: readthedocs-custom-steps  # ...
x-custom-steps:
  - echo "Custom steps to build documentation at $SITE_DIR here"
```

> __Important__: This module should not be installed outside of a Read the Docs build environment.
> It will rename your Python executable and install a substitute. It does not currently provide an
> automated way to revert this change.

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
