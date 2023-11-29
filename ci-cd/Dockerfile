FROM python:3.11-alpine

WORKDIR /ci-cd-fusion-hub-backend
COPY . /ci-cd-fusion-hub-backend

# Install OS Required packages
RUN apk update && apk upgrade && apk add postgresql-dev gcc python3-dev musl-dev linux-headers

# Install Application Required libraries
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8111

CMD ["python", "main.py"]
