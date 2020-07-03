
test:
	docker run --rm -it -v "$(PWD):/opt/src" python:3.7 bash -c " \
		cp -r /opt/src/readthedocs-custom-steps /tmp/rtdcs; \
		rm -rvf /tmp/rtdcs/*.egg-info; \
		READTHEDOCS=True pip install /tmp/rtdcs -q; \
		python -m mkdocs build --readthedocs-custom-steps-version \
	"
