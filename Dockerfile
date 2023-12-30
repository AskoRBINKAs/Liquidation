FROM python:3.10-alpine
EXPOSE 5000
WORKDIR /app
COPY . .
RUN pip3 install -r req.txt
