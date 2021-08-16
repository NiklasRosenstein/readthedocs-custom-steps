
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
    'python:3.6',
    'python:3.7',
    'python:3.8',
    'python:3.9',
  ])
@pytest.mark.parametrize(
  argnames=('command', 'requirements', 'second_line_regex'),
  argvalues=[
    ('mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml', ['mkdocs'], r'python -m mkdocs, version .*$'),
    ('sphinx -T -b html -d _build/doctrees -D language=en . _build/html', ['sphinx'], r'(__main__\.py|sphinx) .*$'),
  ])
def test_mkdocs_hook(python_image: str, command: str, requirements: t.List[str], second_line_regex: str) -> None:
  """
  This unittest uses Docker to test the readthedocs-custom-steps hook, verifying the output from
  the custom steps as well as the reentry into the hook invoking the same command but not running
  into an infinite loop of invoking itself.
  """


  client = docker.from_env()
  with contextlib.ExitStack() as stack:
    tmpfile = stack.enter_context(tempfile.NamedTemporaryFile('w', delete=False))
    stack.callback(Path(tmpfile.name).unlink)
    tmpfile.write(CUSTOM_STEPS_YAML)
    tmpfile.close()

    print("starting container")
    container = client.containers.run(
      python_image,
      volumes={
        PIP_CACHES_VOLUME: {'bind': '/root/.cache/pip', 'mode': 'rw'},
        PROJECT_DIRECTORY: {'bind': '/opt/project', 'mode': 'ro'},
        tmpfile.name: {'bind': '/opt/.readthedocs-custom-steps.yml', 'mode': 'ro'}},
      command=['bash', '-c', textwrap.dedent(f'''
        set -e
        cp -r /opt/project /tmp/rtdcs
        rm -rf /tmp/rtdcs/*.egg-info /tmp/rtdcs/build
        READTHEDOCS=True pip install -q {" ".join(map(shlex.quote, requirements))} /tmp/rtdcs 2>/dev/null
        mkdir /tmp/test; cd /tmp/test; cp /opt/.readthedocs-custom-steps.yml .
        python -m {command}
      ''')],
      detach=False,
      stdin_open=False,
    )

    print("started container")
    stack.callback(lambda: stop_and_remove_container(container))

    print("waiting container")
    exit_code = container.wait()['StatusCode']
    print("done container", exit_code)
    result = container.logs().decode()
    if exit_code != 0:
      print(result)
      raise RuntimeError(f'container returned exit code {exit_code}')

    lines = result.splitlines()
    assert lines[0] == f'rtd-custom-steps says {command}'
    assert re.match(second_line_regex, lines[1]) is not None
