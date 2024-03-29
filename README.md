# E2E-AI-Chatbot 🤖

[**Pipeline**](#pipeline) | [**Installation**](#installation-requirements) | [**User Interface**](#user-interface-app) | [**Model**](#model) | [**Database**](#database) | [**Search**](#search) | [**Contact**](#contact)

[![Flake8 lint](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml/badge.svg)](https://github.com/vnk8071/E2E-AI-Chatbot/actions/workflows/lint.yml)
[![Stargazers][stars-shield]][stars-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

## Overview
End-to-end AI Chatbot is a project that aims to build a chatbot that can answer any question in any domain. The project is built on top of the workflow chatbot Q&A with Gradio and GPT4All model. The project is currently in the development stage.

- Gradio is a Python library that allows you to quickly create customizable UI components around your machine learning models, deep learning models, and other functions. Mix and match components to support any combination of inputs and outputs. Built-in support for NLP, images, plotting, and more.
- GPT4All is an ecosystem to train and deploy powerful and customized large language models that run locally on consumer grade CPUs. Note that your CPU needs to support AVX or AVX2 instructions. The goal is simple - be the best instruction tuned assistant-style language model that any person or enterprise can freely use, distribute and build on. A GPT4All model is a 3GB - 8GB file that you can download and plug into the GPT4All open-source ecosystem software. Nomic AI supports and maintains this software ecosystem to enforce quality and security alongside spearheading the effort to allow any person or enterprise to easily train and deploy their own on-edge large language models.

## Tech Stack
| # | Name | Description |
| :---: | :---: | :---: |
| 1 | Python | Programming language used to build the project. |
| 2 | FastAPI | Web framework backend |
| 3 | Gradio | Backend UI low code |
| 4 | Docker | Package application |
| 5 | GPT4All | Model GPT offline |
| 6 | Redis | Cache chat history |
| 7 | MongoDB | Database save document |
| 8 | Mongo Express | Database UI |
| 9 | Logstash | Data migration |
| 10 | Elasticsearch | Search engine |
| 11 | Kibana | Search monitoring |
| 12 | Nginx | HTTP and reverse proxy server |
| 13 | Kubernetes | Container orchestration |
| 14 | AWS/Azure | Cloud |
| 15 | Pre-commit | Linting |

## Pipeline
### Current:
<img src="https://user-images.githubusercontent.com/78080480/241518928-57c61fef-f4fb-4c17-a095-4748d79c3b87.png">

### Next stage:
- [x] FastAPI & Gradio backend
- [x] Dockerize packages
- [x] Add UI ingest upload file
- [x] Add login page
- [x] Add pre-commit
- [x] Add docs
- [ ] Nginx for http and https
- [ ] K8s
- [ ] CI/CD cloud (AWS/Azure)

## Installation Requirements
- Minimum CPU 8GiB RAM
- Uncomment line 8 packages = [{include = "**"}] to use all internal packages (Passing Flake8)
- Install packages and download GPT4All model by
1. Run locally

With poetry:
```bash
chmod u+x ./setup.sh
bash ./setup.sh
```

With pip:
```bash
pip install poetry
poetry shell
poetry install
```

Build MongoDB, Mongo Express, Logstash, Elasticsearch, Kibana and Redis
```
docker compose -f docker-compose-service.yml up
poetry run python app.py --host 0.0.0.0 --port 8071
```
2. Run docker
```
docker compose up
```
## User Interface App
```
make run
```
Run on: http://localhost:8071

### Login:
```
Account: admin
Password: admin
```

<img src="https://user-images.githubusercontent.com/78080480/274474984-f9902c39-bc0a-42f0-95d0-3fe3c0ebefda.png">

### Chatbot:
<img src="https://user-images.githubusercontent.com/78080480/241147184-0c3bea3e-e19f-4532-863d-d5ddd112dea6.png">

New version:
<img src="https://user-images.githubusercontent.com/78080480/274782483-431171ec-c311-4754-bd58-8fb8ec79afd7.png">

### Ingest PDF:
<img src="https://user-images.githubusercontent.com/78080480/274973411-23083447-f653-4ff4-b03c-57e4c19ac3e5.png">

<p align="right">(<a href="#e2e-ai-chatbot-🤖">back to top</a>)</p>

## Model
1. GPT4ALL: Current best commercially licensable model based on GPT-J and trained by Nomic AI on the latest curated GPT4All dataset.

## Database
1. MongoDB
Run on: http://localhost:27017
```
poetry run python src/ingest_database.py --mongodb-host "mongodb://localhost:27017/" --data-path "static/pdf/"
```
### Mongo Compass (Windows)
<img src="https://user-images.githubusercontent.com/78080480/240465436-6cd732a7-bfd7-41ea-8da5-f7d9e36908fc.png">

### Mongo Express
Run on: http://localhost:8081
<img src="https://user-images.githubusercontent.com/78080480/241128094-d9b4469b-9a1e-4b7f-a0fd-1037a1bdeda5.png">

## Data Migration
Run on: http://localhost:9600

<img src="https://user-images.githubusercontent.com/78080480/241519101-e22b955d-b072-4362-acb3-fe7ad8e7a746.png">

## Search
1. Elasticsearch & Kibana
```
poetry run python src/ingest_search.py --mongodb-host "mongodb://localhost:27017/" --es-host "http://localhost:9200/" --index_name "document"
```
Elasticsearch run on: http://localhost:9200

Kibana run on: http://localhost:5601
<img src="https://user-images.githubusercontent.com/78080480/240532984-f66cc3c3-a20b-4d93-a421-8553cec5dc46.png">

## Cache Chat History
For generating question takes a long time 97(s)/question, we use Redis to cache chat history.
<img src="https://user-images.githubusercontent.com/78080480/274635995-ebb24e0d-1038-47ec-b63e-3ea94eeb67a1.png">

Quickly generate question 0.5(s)/question
<img src="https://user-images.githubusercontent.com/78080480/274638446-c9d7037a-e295-4773-b08e-2bf3996fef2c.png">

## Contact
- KhoiVN - [@linkedin-khoivn8071](https://www.linkedin.com/in/khoivn8071) - nguyenkhoi8071@gmail.com
- Project Link: [Github-E2E-AI-Chatbot](https://github.com/vnk8071/E2E-AI-Chatbot)
- Website: [khoivn.space](https://khoivn.space)
## Impressive
- From Langchain Framework: https://github.com/hwchase17/langchain
- From GPT4All: https://github.com/nomic-ai/gpt4all
<p align="right">(<a href="#e2e-ai-chatbot-🤖">back to top</a>)</p>

[stars-shield]: https://img.shields.io/github/stars/vnk8071/E2E-AI-Chatbot.svg?style=badge
[stars-url]: https://github.com/vnk8071/E2E-AI-Chatbot/stargazers
[license-shield]: https://img.shields.io/github/license/vnk8071/E2E-AI-Chatbot.svg?style=badge
[license-url]: https://github.com/vnk8071/E2e-AI-Chatbot/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/khoivn8071
