ARG PYTHON_VERSION=3.12.1
FROM python:${PYTHON_VERSION}

WORKDIR /usr/src/app

COPY . .

RUN python3 -m pip install -e .[all]

CMD [ "pytest", "./" ]
