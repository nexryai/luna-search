FROM debian:bookworm-slim

WORKDIR /app

COPY requirements.txt /app/

RUN apt update && apt upgrade -y \
 && apt install git python3 python3-venv python3-pip libboost-all-dev mecab mecab-ipadic sqlite3 python3-dev libboost-dev libboost-regex-dev libmecab-dev libsqlite3-dev build-essential -y \
 && pip install --break-system-packages -r requirements.txt \
 && pip install --break-system-packages git+https://github.com/searxng/searxng \
 && apt purge git python3-dev libboost-dev libboost-regex-dev libmecab-dev libsqlite3-dev build-essential -y && apt -y autoremove --purge \
 && groupadd app \
 && useradd -d /app -s /bin/sh -g app app \
 && chown -R app:app /app \
 && su app -c "python3 -m pygeonlp.api setup /usr/pygeonlp_basedata" \
 && apt clean

COPY . .

USER app
CMD [ "gunicorn", "--workers", "4", "--threads", "1", "server:app" ]
