FROM python:3.11-slim

WORKDIR /app

COPY index.html style.css app.js tariffario_pompei.json server_pompei.py /app/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python3", "server_pompei.py"]