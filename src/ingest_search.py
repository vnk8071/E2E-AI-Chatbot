from databases import MongoDBClient
from searchers import ElasticSearch
from loggers import logging_custom

logger = logging_custom()


def main(args):
    mongo_database = MongoDBClient(mongodb_host=args.mongodb_host)
    mongo_database.check_database()
    documents = mongo_database.get_contents()
    es = ElasticSearch(
        elasticsearch_host=args.es_host,
        index_name="document"
    )
    es.add_contents(documents=documents)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongodb-host", default="mongodb://localhost:27017/")
    parser.add_argument("--es-host", default="http://localhost:9200/")
    parser.add_argument("--index_name", default="document")
    args = parser.parse_args()
    main(args)
