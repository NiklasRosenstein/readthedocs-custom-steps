# readthedocs-custom-steps

> __Important__: This module should not be installed outside of a Read the Docs build environment.

Example `.readthedocs.yml`:

```yml
version: 2
mkdocs: {}  # tell readthedocs to use mkdocs
python:
  version: 3.7
  install:
    - requirements: readthedocs-custom-steps  # ...
x-custom-steps:
  - echo "Custom steps to build documentation at $SITE_DIR here"
```

---

<p align="center">Copyright &copy; 2020 Niklas Rosenstein</p>
