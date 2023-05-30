# Using Ubuntu 22.04 LTS
#FROM ubuntu:jammy

# Install system dependencies
#RUN apt update && apt upgrade -y
#RUN apt install nginx -y

FROM python:3.10

# Set up working dir and copy app
RUN mkdir /app
WORKDIR /app
ADD . /app

# Set up Python app environment
RUN pip install --no-cache-dir -r requirements.txt

# Launch
EXPOSE 80
CMD ["gunicorn", "wsgi:application"]
