import argparse
from databases import MongoDBClient
from extractors import PyPDFDirectoryLoader
from loggers import AppLogger

logger = AppLogger().get_logger()
parser = argparse.ArgumentParser()
parser.add_argument("--mongodb-host", default="mongodb://localhost:27017/")
parser.add_argument("--data-path", default="samples/")
args = parser.parse_args()
logger.info(f"MongoDB Host: {args.mongodb_host}")
logger.info(f"Data path: {args.data_path}")


def main(args):
    pdf_loader = PyPDFDirectoryLoader(args.data_path)
    pages = pdf_loader.load_and_split()
    mongo_database = MongoDBClient(mongodb_host=args.mongodb_host)
    mongo_database.check_database()
    for page in pages:
        mongo_database.add_contents(contents=[page.dict()])


if __name__ == '__main__':
    main(args)
