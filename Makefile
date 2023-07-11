all: dist

.PHONY: dist
dist: venv/created
	./venv/bin/python3 setup.py sdist bdist_wheel

.PHONY: lint
lint: venv/created
	./venv/bin/black --check .
	./venv/bin/flake8 .

venv: venv/manifest.txt
venv/manifest.txt: ./requirements_dev.txt ./requirements.txt
	rm -rf venv
	python3 -m venv ./venv
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade wheel
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade\
		-r ./requirements_dev.txt\
		-r ./requirements.txt
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@
	touch venv/created

.PHONY: veryclean
veryclean: clean
veryclean:
	rm -rf venv/

.PHONY: clean
clean:
	rm -rf build/
	rm -rf logs/
	rm -rf dist/
	rm -rf *.egg-info