import os
import shutil

from databases import MongoDBClient
from extractors import PyPDFDirectoryLoader
from loggers import AppLogger
from searchers import ElasticSearch

logger = AppLogger().get_logger()


def save_upload_file(uploaded_files, server_host):
    try:
        for uploaded_file in uploaded_files:
            DATA_PATH = "static/pdf/"
            file_name = os.path.basename(uploaded_file.orig_name)
            logger.info(f"file_name {file_name}")
            shutil.copy(src=uploaded_file.orig_name, dst=f"{DATA_PATH}{file_name}")
        ingest_database(
            server_host=server_host, data_path=DATA_PATH, database_name="document"
        )
        ingest_search(server_host=server_host, index_name="document")
    except Exception as e:
        logger.info("Please check server host")
        logger.error(f"Exception: {e}")


def ingest_database(server_host: str, data_path: str, database_name: str):
    try:
        logger.info(f"Start ingest fodler {data_path} to Mongodb")
        pdf_loader = PyPDFDirectoryLoader(data_path)
        pages = pdf_loader.load_and_split()
        mongo_database = MongoDBClient(
            mongodb_host=server_host.replace("http", "mongodb") + ":27017/",
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


def ingest_search(server_host: str, index_name: str):
    try:
        logger.info("Start ingest data to ElasticSearch")
        mongo_database = MongoDBClient(
            mongodb_host=server_host.replace("http", "mongodb") + ":27017/"
        )
        mongo_database.check_database()
        documents = mongo_database.get_contents()
        es = ElasticSearch(
            elasticsearch_host=server_host + ":9200/", index_name=index_name
        )
        es.add_contents(documents=documents)
        logger.info(
            "Please check Kibana \
        in index {index_name} port 5601"
        )
    except Exception as e:
        logger.info("Please check server host")
        logger.info(f"Exception: {e}")
