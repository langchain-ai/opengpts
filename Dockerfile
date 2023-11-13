FROM python:3.11

RUN apt-get install -y libmagic1

WORKDIR /backend

COPY ./backend .

RUN rm poetry.lock

RUN pip install .

COPY ./frontend/dist ./ui

CMD exec uvicorn app.server:app --host 0.0.0.0 --port $PORT
