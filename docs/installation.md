---
sidebar_label: 'Installation'
sidebar_position: 2
---

# Installation Requirements
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

Build MongoDB, Mongo Express, Logstash, Elasticsearch and Kibana
```
docker compose -f docker-compose-service.yml up
poetry run python app.py --host 0.0.0.0 --port 8071
```
2. Run docker
```
docker compose up
```
