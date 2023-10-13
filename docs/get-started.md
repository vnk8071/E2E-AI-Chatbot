---
sidebar_label: 'Get Started'
sidebar_position: 2
---

# Get Started
## Run locally
```
make run
```

## Run docker compose
```
docker compose up
```

After running the above command, you can access the application at http://localhost:8071

## Login:
![login](https://user-images.githubusercontent.com/78080480/274474984-f9902c39-bc0a-42f0-95d0-3fe3c0ebefda.png)

```
Account: admin
Password: admin
```

## Chat User Interface
Include features:
- Prompt: Instruction chatbot for generate answer
- Config: Config model
- Chat box: Chat with chatbot
- Services button: Redirect to services page (Ingest, Kibana, Mongo Express)
- Version: Note for update version

![ui_new](https://user-images.githubusercontent.com/78080480/274782483-431171ec-c311-4754-bd58-8fb8ec79afd7.png)

## Citation
![citation](https://user-images.githubusercontent.com/78080480/241147184-0c3bea3e-e19f-4532-863d-d5ddd112dea6.png)

## Ingest PDF:
Currently, we support only PDF file format.

![ingest](https://user-images.githubusercontent.com/78080480/274973411-23083447-f653-4ff4-b03c-57e4c19ac3e5.png)

## MongoDB & Express
### Ingest data to MongoDB
```
poetry run python src/ingest_database.py --mongodb-host "mongodb://localhost:27017/" --data-path "static/pdf/"
```
### View data store in MongoDB

![mongo_express](https://user-images.githubusercontent.com/78080480/241128094-d9b4469b-9a1e-4b7f-a0fd-1037a1bdeda5.png)

## Elasticsearch & Kibana
### Ingest data to Elasticsearch engine
```
poetry run python src/ingest_search.py --mongodb-host "mongodb://localhost:27017/" --es-host "http://localhost:9200/" --index_name "document"
```
### View data store in Elasticsearch engine

![kibana](https://user-images.githubusercontent.com/78080480/240532984-f66cc3c3-a20b-4d93-a421-8553cec5dc46.png)

## Cache Chat History
For generating question takes a long time 97(s)/question, we use Redis to cache chat history

![redis_pre](https://user-images.githubusercontent.com/78080480/274635995-ebb24e0d-1038-47ec-b63e-3ea94eeb67a1.png)

Quickly generate question 0.5(s)/question

![redis_after](https://user-images.githubusercontent.com/78080480/274638446-c9d7037a-e295-4773-b08e-2bf3996fef2c.png)
