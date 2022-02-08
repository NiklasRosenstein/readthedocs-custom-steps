
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
    #'python:3.6-alpine',
    #'python:3.7-alpine',
    #'python:3.8-alpine',
    'python:3.9-alpine',
    'python:3.10-alpine',
  ])
@pytest.mark.parametrize(
  argnames='config_dir',
  argvalues=['.', 'docs'],
)
@pytest.mark.parametrize(
  argnames='rtd_config',
  argvalues=[None, READTHEDOCS_CONFIG_YAML],
)
@pytest.mark.parametrize(
  argnames=('steps_filename', 'steps_content'),
  argvalues=[
    ('.readthedocs-custom-steps.yml', READTHEDOCS_CONFIG_YAML),
    ('pyproject.toml', PYPROJECT_TOML),
  ]
)
@pytest.mark.parametrize(
  argnames=('command', 'requirements', 'second_line_regex'),
  argvalues=[
    (
      'mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml',
      ['mkdocs==1.2.3'],
      r'python -m mkdocs, version .*$',
    ),
    (
      'sphinx -T -b html -d _build/doctrees -D language=en . _build/html',
      ['sphinx'],
      r'(__main__\.py|sphinx) .*$',
    ),
  ])
def test_mkdocs_hook(
  python_image: str,
  config_dir: str,
  rtd_config: t.Optional[str],
  command: str,
  requirements: t.List[str],
  second_line_regex: str,
  steps_filename: str,
  steps_content: str,
) -> None:
  """
  This unittest uses Docker to test the readthedocs-custom-steps hook, verifying the output from
  the custom steps as well as the reentry into the hook invoking the same command but not running
  into an infinite loop of invoking itself.
  """


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

    if rtd_config:
      tmpfile = stack.enter_context(tempfile.NamedTemporaryFile('w', delete=False))
      stack.callback(Path(tmpfile.name).unlink)
      tmpfile.write(rtd_config)
      tmpfile.close()
      volumes[tmpfile.name] = {'bind': '/opt/.readthedocs.yml', 'mode': 'ro'}

    container = client.containers.run(
      python_image,
      volumes=volumes,
      command=['sh', '-c', textwrap.dedent(f'''
        set -e
        cp -r /opt/project /tmp/rtdcs
        rm -rf /tmp/rtdcs/*.egg-info /tmp/rtdcs/build

        # Install rtd-cs
        python -m pip install --upgrade pip
        python -m pip install PyYAML
        READTHEDOCS=True pip install {" ".join(map(shlex.quote, requirements))} /tmp/rtdcs -v 1>&2

        # Setup test directory
        mkdir /tmp/test; cd /tmp/test;
        if [ -f /opt/.readthedocs.yml ]; then cp /opt/.readthedocs.yml .; fi
        mkdir -p {config_dir}
        cp /opt/.readthedocs-custom-steps.yml {config_dir}

        # Link shim to test if rtd-cs detects it
        mkdir -p /root/.pyenv/shims
        ln -s "$(which python)" /root/.pyenv/shims/python3.7

        # Invoke build command, which should trigger rtd-cs
        python -m {command}
      ''')],
      detach=True,
      stdin_open=False,
    )

    #stack.callback(lambda: stop_and_remove_container(container))

    exit_code = container.wait()['StatusCode']
    result = container.logs().decode()
    if exit_code != 0:
      print(result)
      raise RuntimeError(f'container returned exit code {exit_code}')

    lines = result.splitlines()
    assert lines[0] == f'rtd-custom-steps says {command}'
    assert re.match(second_line_regex, lines[1]) is not None
    assert lines[2] == '/root/.pyenv/shims/python3.7'
