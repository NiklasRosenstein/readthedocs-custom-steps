# This file was auto-generated by Shut. DO NOT EDIT
# For more information about Shut, check out https://pypi.org/project/shut/

from __future__ import print_function
from setuptools.command.install import install as _install_command
import io
import os
import setuptools
import sys

install_hooks = {
  "before-install": [
    [
      "bin/install-hack.py"
    ]
  ],
  "after-install": [],
  "before-develop": [],
  "after-develop": []
}

def _run_hooks(event):
  import subprocess, shlex, os
  def _shebang(fn):
    with open(fn) as fp:
      line = fp.readline()
      if line.startswith('#'):
        return shlex.split(line[1:].strip())
      return []
  for command in install_hooks[event]:
    if command[0].endswith('.py') or 'python' in _shebang(command[0]):
      command.insert(0, sys.executable)
    env = os.environ.copy()
    env['SHUT_INSTALL_HOOK_EVENT'] = event
    res = subprocess.call(command, env=env)
    if res != 0:
      raise RuntimeError('command {!r} returned exit code {}'.format(command, res))

class install_command(_install_command):
  def run(self):
    _run_hooks('before-install')
    super(install_command, self).run()
    _run_hooks('after-install')

readme_file = 'readme.md'
if os.path.isfile(readme_file):
  with io.open(readme_file, encoding='utf8') as fp:
    long_description = fp.read()
else:
  print("warning: file \"{}\" does not exist.".format(readme_file), file=sys.stderr)
  long_description = None

requirements = [
  'PyYAML >=5.0.0',
  'tomli >=1.2.3',
]
test_requirements = [
  'docker >=5.0.0,<6.0.0',
  'six',
  'types-PyYAML',
]
extras_require = {}
extras_require['test'] = test_requirements

setuptools.setup(
  name = 'readthedocs-custom-steps',
  version = '0.6.2',
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  description = 'A hack to run custom steps when building documentation on Read the Docs.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  url = 'https://github.com/NiklasRosenstein/readthedocs-custom-steps/',
  license = 'MIT',
  py_modules = ['readthedocs_custom_steps'],
  package_dir = {'': 'src'},
  include_package_data = True,
  install_requires = requirements,
  extras_require = extras_require,
  tests_require = test_requirements,
  python_requires = '>=3.5.0,<4.0.0',
  data_files = [],
  entry_points = {},
  cmdclass = {'install': install_command},
  keywords = [],
  classifiers = [],
  zip_safe = True,
)
