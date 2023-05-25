# E2E-AI-Chatbot 🤖

[**Pipeline**](#pipeline) | [**Installation**](#installation-requirements) | [**UI Chatbot**](#ui-chatbot) | [**Model**](#model) | [**Database**](#database) | [**Search**](#search)


[![Flake8 lint](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml/badge.svg)](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml)


## Pipeline

## Installation Requirements
- Minimum CPU 8GiB RAM
- Install packages and download GPT4All model by
```bash
chmod u+x ./setup.sh
bash ./setup.sh
```
- Build MongoDB, Elasticsearch and Kibana
```
docker compose -f docker/docker-compose.yml up
```

## UI Chatbot
```
poetry run python src/ui_chatbot.py --server-name "0.0.0.0" --server-port 8071
```
Run on: http://localhost:8071
<img src="https://user-images.githubusercontent.com/78080480/239847294-c07ef89d-c584-4e34-9697-f507ddd01882.PNG">

## Model
1. GPT4ALL: Current best commercially licensable model based on GPT-J and trained by Nomic AI on the latest curated GPT4All dataset.

## Database
1. MongoDB
```
mongoDB_host = "mongodb://localhost:27017/"
poetry run python src/ingest_database.py --mongodb-host "mongodb://localhost:27017/" --data-path "samples/"
```
Run on: http://localhost:27017
<img src="https://user-images.githubusercontent.com/78080480/240465436-6cd732a7-bfd7-41ea-8da5-f7d9e36908fc.png">

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