# This file was automatically generated by Shore. Do not edit manually.
# For more information on Shore see https://pypi.org/project/nr.shore/

from __future__ import print_function
from setuptools.command.install import install as _install_command
from setuptools.command.develop import develop as _develop_command
import io
import os
import re
import setuptools
import sys

install_hooks = [
  {"command": ["bin/install-hack.py"], "event": "install"},
]

def _run_hooks(event):
  import subprocess, shlex, os
  def _shebang(fn):
    with open(fn) as fp:
      line = fp.readline()
      if line.startswith('#'):
        return shlex.split(line[1:].strip())
      return []
  for hook in install_hooks:
    if not hook['event'] or hook['event'] == event:
      command = [x.replace('$SHORE_INSTALL_HOOK_EVENT', event) for x in hook['command']]
      if command[0].endswith('.py') or 'python' in _shebang(command[0]):
        command.insert(0, sys.executable)
      env = os.environ.copy()
      env['SHORE_INSTALL_HOOK_EVENT'] = event
      res = subprocess.call(command, env=env)
      if res != 0:
        raise RuntimeError('command {!r} returned exit code {}'.format(command, res))

class install_command(_install_command):
  def run(self):
    _run_hooks('install')
    super(install_command, self).run()
    _run_hooks('post-install')

with io.open('src/readthedocs_custom_steps.py', encoding='utf8') as fp:
  version = re.search(r"__version__\s*=\s*'(.*)'", fp.read()).group(1)

readme_file = 'README.md'
source_readme_file = '../README.md'
if not os.path.isfile(readme_file) and os.path.isfile(source_readme_file):
  import shutil; shutil.copyfile(source_readme_file, readme_file)
  import atexit; atexit.register(lambda: os.remove(readme_file))

if os.path.isfile(readme_file):
  with io.open(readme_file, encoding='utf8') as fp:
    long_description = fp.read()
else:
  print("warning: file \"{}\" does not exist.".format(readme_file), file=sys.stderr)
  long_description = None

requirements = ['PyYAML >=5.0,<6.0.0']

setuptools.setup(
  name = 'readthedocs-custom-steps',
  version = version,
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  description = 'A hack to run custom steps when building documentation on Read the Docs.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  url = None,
  license = None,
  py_modules = ['readthedocs_custom_steps'],
  package_dir = {'': 'src'},
  include_package_data = True,
  install_requires = requirements,
  extras_require = {},
  tests_require = [],
  python_requires = None, # TODO: '>=3.5,<4.0.0',
  data_files = [],
  entry_points = {},
  cmdclass = {'install': install_command},
  keywords = [],
  classifiers = [],
)
