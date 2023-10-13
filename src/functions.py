import os
import shutil

from databases import MongoDBClient
from extractors import PyPDFDirectoryLoader
from loggers import AppLogger
from searchers import ElasticSearch
from config import settings

logger = AppLogger().get_logger()


def save_upload_file(uploaded_files):
    for uploaded_file in uploaded_files:
        file_name = os.path.basename(uploaded_file.name)
        logger.info(f"file_name {file_name}")
        shutil.copy(src=uploaded_file.orig_name, dst=f"{settings.DATA_PATH}{file_name}")


def ingest_database(database_name: str):
    try:
        logger.info(f"Start ingest fodler {settings.DATA_PATH} to Mongodb")
        pdf_loader = PyPDFDirectoryLoader(settings.DATA_PATH)
        pages = pdf_loader.load_and_split()
        mongo_database = MongoDBClient(
            mongodb_host=settings.SERVER_HOST.replace("http", "mongodb") + ":27017/",
            database_name=database_name,
        )
        mongo_database.check_database()
        for page in pages:
            mongo_database.add_contents(contents=[page.dict()])
        logger.info(
            "Please check Mongo express \
        in database {database_name} with port 8081"
        )
    except Exception as e:
        logger.info("Please check server host")
        logger.info(f"Exception: {e}")


def ingest_search(index_name: str):
    try:
        logger.info("Start ingest data to ElasticSearch")
        mongo_database = MongoDBClient(
            mongodb_host=settings.SERVER_HOST.replace("http", "mongodb") + ":27017/"
        )
        mongo_database.check_database()
        documents = mongo_database.get_contents()
        es = ElasticSearch(
            elasticsearch_host=settings.SERVER_HOST + ":9200/", index_name=index_name
        )
        es.add_contents(documents=documents)
        logger.info(
            "Please check Kibana \
        in index {index_name} port 5601"
        )
    except Exception as e:
        logger.info("Please check server host")
        logger.info(f"Exception: {e}")
