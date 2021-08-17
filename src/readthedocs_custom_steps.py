
import logging
import os
import re
import subprocess
import sys
import typing as t
from pathlib import Path

import yaml

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.4.0'

log = logging.getLogger(__name__)
PYENV_SHIMS_DIR = Path('/home/docs/.pyenv/shims')
READTHEDOCS_CONFIG = Path('.readthedocs.yml')
READTHEDOCS_CS_CONFIG = Path('.readthedocs-custom-steps.yml')


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
  Finds the Rtd-CS config file.
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
    match = re.match(r'python3\.(\d+)', path.name)
    if match:
      result[(3, int(match.group(1)))] = str(path)

  return result


def main():
  argv = sys.argv[1:]
  if argv and argv[0] in ('-v', '--version'):
    print('readthedocs-custom-steps', __version__)
    return

  config_file = find_config_file()
  steps = yaml.safe_load(config_file.read_text())['steps']

  env = os.environ.copy()

  shims = find_pyenv_shims()
  if shims:
    env.update({f'PYTHON{x}{y}': p for (x, y), p in shims.items()})
    env['PYTHON'] = shims[max(shims)]

  bash_script = '\n'.join(['set -e'] + steps)
  sys.exit(subprocess.call(['bash', '-c', bash_script] + sys.argv, env=env))


if __name__ == '__main__':
  main()
