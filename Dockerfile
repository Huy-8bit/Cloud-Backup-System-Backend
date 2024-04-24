FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN python -m venv virtualenv

RUN /bin/bash -c "source virtualenv/bin/activate"

RUN pip install -r requirements.txt

COPY . .

CMD ["python3.11", "client/client.py"]