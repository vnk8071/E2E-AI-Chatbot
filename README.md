# E2E-AI-Chatbot 🤖
Description: Pipeline offline of using GPT4ALL model combine with own context for generating answer.

[**Pipeline**](#pipeline) | [**Installation**](#installation-requirements) | [**UI Chatbot**](#ui-chatbot) | [**Model**](#models) | [**Database**](#databases)

[![Flake8 lint](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml/badge.svg)](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml)


## Pipeline

## Installation Requirements
- Minimum CPU 8GiB RAM
- Install packages and download GPT4All model by
```bash
chmod u+x ./setup.sh
bash ./setup.sh
```

## UI Chatbot
```
poetry run python ui_chatbot.py
```
<img src="https://user-images.githubusercontent.com/78080480/239847294-c07ef89d-c584-4e34-9697-f507ddd01882.PNG">

## Models
1. GPT4ALL: Current best commercially licensable model based on GPT-J and trained by Nomic AI on the latest curated GPT4All dataset.

## Databases
1. MongoDB
```
mongoDB_host = "mongodb://localhost:27017/"
poetry run python ingest_database.py --mongodb-host "mongodb://localhost:27017/" --data-path "samples/"
```
<img src="https://user-images.githubusercontent.com/78080480/240465436-6cd732a7-bfd7-41ea-8da5-f7d9e36908fc.png">

## Impressive
- From Langchain Framework: https://github.com/hwchase17/langchain
- From GPT4All: https://github.com/nomic-ai/gpt4all
```
@misc{gpt4all,
  author = {Yuvanesh Anand and Zach Nussbaum and Brandon Duderstadt and Benjamin Schmidt and Andriy Mulyar},
  title = {GPT4All: Training an Assistant-style Chatbot with Large Scale Data Distillation from GPT-3.5-Turbo},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/nomic-ai/gpt4all}},
}
```