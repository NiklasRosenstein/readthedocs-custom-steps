
import logging
import os
import re
import subprocess
import sys
import textwrap
import typing as t
from pathlib import Path

import tomli
import yaml

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.6.2'

log = logging.getLogger(__name__)
PYENV_SHIMS_DIR = Path(os.path.expanduser('~')) / '.pyenv/shims'
READTHEDOCS_CONFIG = Path('.readthedocs.yml')
READTHEDOCS_CS_CONFIG = Path('.readthedocs-custom-steps.yml')
PYPROJECT_TOML = Path('pyproject.toml')


def get_referenced_requirements_files() -> t.List[str]:
  """
  Reads the Read the Docs configuration file and extracts all filenames referenced in
  `$.python.install[*].requirements` config values.
  """

  if not READTHEDOCS_CONFIG.exists():
    return []

  config = yaml.safe_load(READTHEDOCS_CONFIG.read_text())
  install = config.get('python', {}).get('install', [])
  requirements: t.List[t.Optional[str]]= [x.get('requirements') for x in install]
  return [x for x in requirements if x]


def find_config_file() -> Path:
  """
  Finds the RtdCS config file.
  """

  choices: t.List[Path] = []

  for directory in [Path('.'), Path('docs')] + [Path(f).parent for f in get_referenced_requirements_files()]:
    path = (Path(directory) / READTHEDOCS_CS_CONFIG).resolve()
    if path.exists():
      return path
    if path not in choices:
      choices.append(path)

  raise RuntimeError(f'file {READTHEDOCS_CS_CONFIG} could not be found, searched in\n- ' + '\n- '.join(map(str, choices)))


def find_pyenv_shims() -> t.Dict[t.Tuple[int, int], str]:
  """
  Finds Python shims in `/home/docs/.pyenv/shims` and returns a dictionary mapping Python major.minor version
  pairs to the full path.
  """

  if not PYENV_SHIMS_DIR.is_dir():
    return {}

  result = {}
  for path in PYENV_SHIMS_DIR.iterdir():
    match = re.match(r'^python3\.(\d+)$', path.name)
    if match:
      result[(3, int(match.group(1)))] = str(path)

  return result


def main():
  argv = sys.argv[1:]
  if argv and argv[0] in ('-v', '--version'):
    print('readthedocs-custom-steps', __version__)
    return

  if PYPROJECT_TOML.exists():
    config = tomli.loads(PYPROJECT_TOML.read_text()).get('tool', {}).get('readthedocs-custom-steps')
    filename = PYPROJECT_TOML
  else:
    config = None
    filename = None

  if config is None:
    filename = find_config_file()
    config = yaml.safe_load(filename.read_text())

  env = os.environ.copy()
  shims = find_pyenv_shims()
  if shims:
    env.update({f'PYTHON{x}{y}': p for (x, y), p in shims.items()})
    env['PYTHON'] = shims[max(shims)]

  shell = os.getenv('SHELL', '/bin/sh')
  bash_script = 'set -e\n'
  if 'steps' in config:
    assert isinstance(config['steps'], list)
    bash_script += '\n'.join(config['steps'])
  elif 'script' in config:
    bash_script += textwrap.dedent(config['script'])
  else:
    raise RuntimeError(f'configuration "{filename}" contains no "script" or "steps" key')

  command = [shell, '-c', bash_script] + sys.argv
  print('[readthedocs-custom-steps dispatch]: running', command, file=sys.stderr)

  sys.exit(subprocess.call(command, env=env))


if __name__ == '__main__':
  main()
