
import contextlib
import re
import shlex
import textwrap
import tempfile
import typing as t
from pathlib import Path
import docker  # type: ignore
import pytest

PIP_CACHES_VOLUME = 'pip-caches'
PROJECT_DIRECTORY = str(Path(__file__).parent.parent.resolve())
CUSTOM_STEPS_YAML = '''
steps:
- echo rtd-custom-steps says "$@"
- python -m "${1}" --version
- echo $PYTHON
'''
READTHEDOCS_CONFIG_YAML = '''
python:
  install:
    - requirements: rtd/requirements.txt
'''
PYPROJECT_TOML = '''
[tool.readthedocs-custom-steps]
script = """
echo rtd-custom-steps says "$@"
python -m "${1}" --version
echo $PYTHON
"""
'''


def stop_and_remove_container(container):
  try:
    container.reload()
    if container.status == 'running':
      container.stop()
    container.reload()
    if container.status == 'running':
      container.kill()
  finally:
    container.remove()


@pytest.mark.parametrize(
  argnames='python_image',
  argvalues=[
    '3.6-alpine',
    '3.7-alpine',
    '3.8-alpine',
    '3.9-alpine',
    '3.10-alpine',
  ],
)
@pytest.mark.parametrize(
  argnames='config_type',
  argvalues=['CustomFile:$pwd', 'CustomFile:docs', 'Pyproject:$pwd'],
)
@pytest.mark.parametrize(
  argnames='with_rtd_config',
  argvalues=['WithRtdConfig', 'WithoutRtdConfig'],
)
@pytest.mark.parametrize(
  argnames='tool',
  argvalues=['mkdocs', 'sphinx'],
)
def test_mkdocs_hook(
  python_image: str,
  config_type: str,
  with_rtd_config: bool,
  tool: str,
) -> None:
  """
  This unittest uses Docker to test the readthedocs-custom-steps hook, verifying the output from
  the custom steps as well as the reentry into the hook invoking the same command but not running
  into an infinite loop of invoking itself.
  """

  config_type, config_dir = config_type.split(':')

  if config_type == 'CustomFile':
    steps_content = CUSTOM_STEPS_YAML
    steps_filename = '.readthedocs-custom-steps.yml'
  else:
    steps_content = PYPROJECT_TOML
    steps_filename = 'pyproject.toml'

  if tool == 'mkdocs':
    command = 'mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml'
    requirements = ['mkdocs==1.2.3']
    second_line_regex = r'python -m mkdocs, version .*$'
  else:
    command = 'sphinx -T -b html -d _build/doctrees -D language=en . _build/html'
    requirements = ['sphinx']
    second_line_regex = r'(__main__\.py|sphinx) .*$'

  if config_dir == '$pwd':
    config_dir = '.'

  client = docker.from_env()
  with contextlib.ExitStack() as stack:
    tmpfile = stack.enter_context(tempfile.NamedTemporaryFile('w', delete=False))
    stack.callback(Path(tmpfile.name).unlink)
    tmpfile.write(steps_content)
    tmpfile.close()

    volumes = {
      PIP_CACHES_VOLUME: {'bind': '/root/.cache/pip', 'mode': 'rw'},
      PROJECT_DIRECTORY: {'bind': '/opt/project', 'mode': 'ro'},
      tmpfile.name: {'bind': f'/opt/{steps_filename}', 'mode': 'ro'}}

    if with_rtd_config == 'WithRtdConfig':
      tmpfile = stack.enter_context(tempfile.NamedTemporaryFile('w', delete=False))
      stack.callback(Path(tmpfile.name).unlink)
      tmpfile.write(READTHEDOCS_CONFIG_YAML)
      tmpfile.close()
      volumes[tmpfile.name] = {'bind': '/opt/.readthedocs.yml', 'mode': 'ro'}

    container = client.containers.run(
      'python:' + python_image,
      volumes=volumes,
      command=['sh', '-c', textwrap.dedent(f'''
        set -e
        cp -r /opt/project /tmp/rtdcs
        rm -rf /tmp/rtdcs/*.egg-info /tmp/rtdcs/build

        # Install rtd-cs
        READTHEDOCS=True pip install {" ".join(map(shlex.quote, requirements))} /tmp/rtdcs -v 1>&2

        # Setup test directory
        mkdir /tmp/test; cd /tmp/test;
        if [ -f /opt/.readthedocs.yml ]; then cp /opt/.readthedocs.yml .; fi
        mkdir -p {config_dir}
        cp /opt/{steps_filename} {config_dir}

        # Link shim to test if rtd-cs detects it
        mkdir -p /root/.pyenv/shims
        ln -s "$(which python)" /root/.pyenv/shims/python3.7

        # Invoke build command, which should trigger rtd-cs
        python -m {command}
      ''')],
      detach=True,
      stdin_open=False,
    )

    stack.callback(lambda: stop_and_remove_container(container))

    exit_code = container.wait()['StatusCode']
    result = container.logs().decode()
    print(result)
    if exit_code != 0:
      raise RuntimeError(f'container returned exit code {exit_code}')

    lines = result.splitlines()
    lines = [l for l in lines if not l.startswith('[readthedocs-custom-steps')]
    assert lines[-3] == f'rtd-custom-steps says {command}', lines[-3]
    assert re.match(second_line_regex, lines[-2]) is not None, lines[-2]
    assert lines[-1] == '/root/.pyenv/shims/python3.7', lines[-1]
