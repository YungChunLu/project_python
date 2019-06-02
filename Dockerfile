FROM python:3.6.7-slim
WORKDIR /app
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 8080
CMD [ "python", "server.py"]