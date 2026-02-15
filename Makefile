.PHONY: install run docker-build docker-run

install:
\tpython -m venv .venv && \\
\t. .venv/bin/activate && \\
\tpip install -r requirements.txt

run:
\tstreamlit run app.py

docker-build:
\tdocker build -t twincell:latest .

docker-run:
\tdocker run --rm -p 8501:8501 twincell:latest
