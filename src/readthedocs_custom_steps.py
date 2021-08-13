
import os
import yaml
import subprocess
import sys
import typing as t

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.4.0'


def load_custom_steps() -> t.List[str]:
  filename = '.readthedocs-custom-steps.yml'
  if os.path.isfile(filename):
    with open(filename) as fp:
      steps = yaml.safe_load(fp)['steps']
  else:
    with open('.readthedocs.yml') as fp:
      config = yaml.safe_load(fp)
    # NOTE: Read the Docs does not currently support custom keys in the configuration.
    #   We keep this code in case it allows custom keys in the future.
    if 'x-custom-steps' not in config:
      sys.exit('error: missing file "{}" or key "x-custom-steps" in ".readthedocs.yml"'.format(filename))
    steps = config['x-custom-steps']
  return steps


def main():
  argv = sys.argv[1:]
  if argv and argv[0] in ('-v', '--version'):
    print('readthedocs-custom-steps', __version__)
    return

  steps = load_custom_steps()
  bash_script = '\n'.join(['set -e'] + steps)
  sys.exit(subprocess.call(['bash', '-c', bash_script] + sys.argv))


if __name__ == '__main__':
  main()
