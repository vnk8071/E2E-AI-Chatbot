# E2E-AI-Chatbot 🤖

[**Pipeline**](#pipeline) | [**Installation**](#installation-requirements) | [**UserInterface**](#user-interface) | [**Model**](#model) | [**Database**](#database) | [**Search**](#search)


[![Flake8 lint](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml/badge.svg)](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml)


## Pipeline

## Installation Requirements
- Minimum CPU 8GiB RAM
- Uncomment line 8 packages = [{include = "**"}] to use all internal packages (Passing Flake8)
- Install packages and download GPT4All model by
```bash
chmod u+x ./setup.sh
bash ./setup.sh
```
- Build MongoDB, Mongo Express, Elasticsearch and Kibana
```
docker compose -f docker/docker-compose.yml up
```

## User Interface App
```
poetry run python app.py --host 0.0.0.0 --port 8071
```
Run on: http://localhost:8071
<img src="https://user-images.githubusercontent.com/78080480/241147184-0c3bea3e-e19f-4532-863d-d5ddd112dea6.png">

## Model
1. GPT4ALL: Current best commercially licensable model based on GPT-J and trained by Nomic AI on the latest curated GPT4All dataset.

## Database
1. MongoDB
Run on: http://localhost:27017
```
mongoDB_host = "mongodb://localhost:27017/"
poetry run python src/ingest_database.py --mongodb-host "mongodb://localhost:27017/" --data-path "samples/"
```
Mongo Compass (Windows)
<img src="https://user-images.githubusercontent.com/78080480/240465436-6cd732a7-bfd7-41ea-8da5-f7d9e36908fc.png">

Mongo Express
Run on: http://localhost:8081
<img src="https://user-images.githubusercontent.com/78080480/241128094-d9b4469b-9a1e-4b7f-a0fd-1037a1bdeda5.png">
## Search
1. Elasticsearch & Kibana
```
elastic_host = "http://localhost:9200/"
poetry run python src/ingest_search.py --mongodb-host "mongodb://localhost:27017/" --es-host "http://localhost:9200/" --index_name "document"
```
Run on: http://localhost:9200
<img src="https://user-images.githubusercontent.com/78080480/240532984-f66cc3c3-a20b-4d93-a421-8553cec5dc46.png">

## Impressive
- From Langchain Framework: https://github.com/hwchase17/langchain
- From GPT4All: https://github.com/nomic-ai/gpt4all
```
@misc{inherit-gpt4all,
  author = {KhoiVN},
  title = {Pipeline offine AI Chatbot using GPT4All model},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/vnk8071/E2E-AI-Chatbot}},
}
```