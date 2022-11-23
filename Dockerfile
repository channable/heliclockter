FROM python:3.11.0

WORKDIR /usr/src/app

COPY . .

RUN python3 -m pip install -e .[all]

CMD [ "pytest", "./" ]
