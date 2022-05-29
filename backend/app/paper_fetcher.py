import time
import os
import sys
import logging
import requests

import schedule

import fetch_papers
from utils import Config
from tfidf import compute_tfidf_vectorization, compute_tfidf_vectorization_authors


def flush_tfidf_cache(config):
    logger.info('Flushing tfidf cache')
    requests.post('http://' + config.backend + '/admin/flush')


def run_paper_ingress():
    fetch_papers.fetch_papers(config)
    compute_tfidf_vectorization_authors(config)
    compute_tfidf_vectorization(config)
    flush_tfidf_cache(config)


if __name__ == '__main__':

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(__name__)

    config = Config(os.getenv('CONFIG_PATH'))

    logger.info('Running initial papers fetch')
    run_paper_ingress()

    logger.info('Fetching papers daily at {}'.format(config.daily_fetch_time))
    schedule.every().day.at(config.daily_fetch_time).do(run_paper_ingress)

    while True:
        schedule.run_pending()
        time.sleep(1)
