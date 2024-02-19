# 🦝 Racoon
#
# Author: Luka Kovacic <luka.kovacic@archq.io>

tox_working_directory = .tox

init:
ifdef PIP_ARGS
	pip install $(PIP_ARGS) -r requirements.txt
else
	pip install -r requirements.txt
endif
tox:
ifndef ENV
	$(error ENV is required for indicating the supported Tox environments.)
endif
ifdef PIP_ARGS
	pip install $(PIP_ARGS) tox flake8
else
	pip install tox flake8
endif
	tox -e $(ENV)
build:
ifdef PIP_ARGS
	pip install $(PIP_ARGS) build
else
	pip install build
endif
	python -m build
release-metadata:
	mkdir release
	./tools/generate-release-markdown.sh release/release-template.md
package: tox build release-metadata
test: tox
clean:
	rm -rf dist
	rm -rf release
