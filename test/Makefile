
.PHONY: test
test:
	docker run --rm -it -v "$(PWD):/opt/src" -v pip-caches:/root/.cache/pip python:3.7 bash -c " \
		set -e; \
		cp -r /opt/src/readthedocs-custom-steps /tmp/rtdcs; \
		rm -rvf /tmp/rtdcs/*.egg-info /tmp/rtdcs/build; \
		READTHEDOCS=True pip install /tmp/rtdcs; \
		mkdir /tmp/test; cd /tmp/test; cp /opt/src/test/.readthedocs-custom-steps.yml .; \
		python -m mkdocs build --clean --site-dir _site/html --config-file mkdocs.yml; \
	"
