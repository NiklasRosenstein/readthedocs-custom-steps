
import textwrap
from pathlib import Path
import docker  # type: ignore
import pytest

PIP_CACHES_VOLUME = 'pip-caches'
PROJECT_DIRECTORY = str(Path(__file__).parent.parent.parent.resolve())


@pytest.mark.parametrize(
  argnames='python_image',
  argvalues=[
    'python:3.6',
    #'python:3.7',
    #'python:3.8',
    #'python:3.9',
  ])
@pytest.mark.parametrize(
  argnames='command',
  argvalues=[
    'mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml',
    'sphinx -T -b html -d _build/doctrees -D language=en . _build/html',
  ])
def test_mkdocs_hook(python_image: str, command: str) -> None:
  client = docker.from_env()
  container = client.containers.run(
    python_image,
    volumes={
      PIP_CACHES_VOLUME: {'bind': '/root/.cache/pip', 'mode': 'rw'},
      PROJECT_DIRECTORY: {'bind': '/opt/project', 'mode': 'ro'}},
    command=['bash', '-c', textwrap.dedent(f'''
      set -e
      cp -r /opt/project /tmp/rtdcs
      rm -rf /tmp/rtdcs/*.egg-info /tmp/rtdcs/build
      READTHEDOCS=True pip install -q /tmp/rtdcs 2>/dev/null
      mkdir /tmp/test; cd /tmp/test; cp /opt/project/src/test/.readthedocs-custom-steps.yml .
      python -m {command}
    ''')],
    detach=True,
    stdin_open=False,
  )
  try:
    exit_code = container.wait()['StatusCode']
    result = container.logs().decode()
    if exit_code != 0:
      print(result)
      raise RuntimeError(f'container returned exit code {exit_code}')
    assert result.rstrip() == f'rtd-custom-steps say {command}'
  finally:
    container.remove()
