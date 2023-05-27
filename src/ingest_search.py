import argparse
from databases import MongoDBClient
from searchers import ElasticSearch
from loggers import AppLogger

logger = AppLogger().get_logger()
parser = argparse.ArgumentParser()
parser.add_argument("--mongodb-host", default="mongodb://localhost:27017/")
parser.add_argument("--es-host", default="http://localhost:9200/")
parser.add_argument("--index-name", default="document")
args = parser.parse_args()
logger.info(f"MongoDB Host: {args.mongodb_host}")
logger.info(f"ElasticSearch Host: {args.es_host}")
logger.info(f"Index name: {args.index_name}")


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
    main(args)
