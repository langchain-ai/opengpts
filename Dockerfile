FROM python:3.11

RUN apt update && apt-get install -y libmagic1 nodejs npm

RUN npm install --global yarn

COPY ./frontend .

WORKDIR /frontend

RUN yarn

RUN yarn run build

COPY ./frontend/dist ./ui

WORKDIR /backend

RUN rm -rf /frontend

COPY ./backend .

RUN rm poetry.lock

RUN pip install -r requirements.txt

CMD exec uvicorn app.server:app --host 0.0.0.0 --port $PORT
