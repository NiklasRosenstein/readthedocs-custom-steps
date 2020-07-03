
import argparse
import os
import yaml
import subprocess
import sys

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '0.1.0'


def main():
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='command')
  build = subparsers.add_parser('build')
  build.add_argument('--clean', action='store_true')
  build.add_argument('--site-dir')
  build.add_argument('--config-file')
  build.add_argument('--readthedocs-custom-steps-version', action='store_true',
    help='Prints the version of the package. This is mainly used to test the hook that is '
         'installed with this packages which catches "python -m mkdocs build".')
  args = parser.parse_args()

  if not args.command:
    parser.print_usage()
    sys.exit(1)

  if args.readthedocs_custom_steps_version:
    print('readthedocs-custom-steps', __version__)
    return

  with open('.readthedocs.yml') as fp:
    config = yaml.safe_load(fp)

  if 'x-custom-steps' not in config:
    sys.exit('error: expected key "x-custom-steps" in .readthedocs.yml')

  os.environ['SITE_DIR'] = args.site_dir
  os.environ['MKDOCS_CONFIG_FILE'] = args.config_file

  bash_script = '\n'.join(['set -e'] + config['x-custom-steps'])
  sys.exit(subprocess.call(['bash', '-c', bash_script]))


if __name__ == '__main__':
  main()
