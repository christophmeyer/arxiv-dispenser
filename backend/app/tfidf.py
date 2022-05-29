import os
import re
import pickle
import logging

from sklearn.feature_extraction.text import (TfidfTransformer, CountVectorizer,
                                             HashingVectorizer)
from sklearn.pipeline import Pipeline
import numpy as np

from paper_processing import paper_id_to_file_name
from database import Paper, create_db_session, get_db_string
from constants import FilenameConstants as FC

logger = logging.getLogger(__name__)


class FullTextDataset():

    def __init__(self, full_text_dir, metadata_dir):
        logger.info('loading full-text dataset')
        metadata_file_paths = os.listdir(metadata_dir)
        self.file_paths = []
        self.ids = []

        for metadata_file_path in metadata_file_paths:
            with open(os.path.join(metadata_dir, metadata_file_path),
                      'rb') as file:
                metadata_dict = pickle.load(file)

            pdf_filename = paper_id_to_file_name(metadata_dict)
            pickle_basename_wo_version = pdf_filename.split('v')[0]

            for version in range(1, 10):
                pickle_filename = pickle_basename_wo_version + 'v{}.pkl'.format(
                    version)
                full_text_file_path = os.path.join(full_text_dir,
                                                   pickle_filename)
                if os.path.exists(full_text_file_path):
                    self.file_paths.append(
                        os.path.join(full_text_dir, pickle_filename))
                    self.ids.append(metadata_dict['id'])

    def get_generator(self):
        counter = 0
        for file_path in self.file_paths:
            if counter % 1000 == 0:
                logger.info('Processing {}/{}'.format(counter,
                                                      len(self.file_paths)))
            with open(file_path, 'rb') as file:
                paper_pdf = pickle.load(file)

            raw_text = ' '.join(list(paper_pdf))
            processed_text = re.sub(r'[^a-zA-Z0-9_\s]', '',
                                    re.sub(r'\s+', ' ', raw_text)).lower()
            counter += 1
            yield processed_text


class AuthorsDataset():

    def __init__(self, db_session):
        self.db_query = db_session.query(Paper)
        self.ids = []

    def get_generator(self):
        for paper in self.db_query:
            for author in paper.authors:
                self.ids.append(paper.idx)
                processed_text = re.sub(r'[^a-zA-Z0-9_\s]', '',
                                        re.sub(r'\s+', ' ',
                                               author['name'])).lower()
                yield processed_text


def compute_tfidf_vectorization(config):
    logger.info('computing tfidf vectorization for papers')
    dataset = FullTextDataset(config.full_text_dir, config.metadata_dir)

    pipeline = Pipeline([('hashvec',
                          HashingVectorizer(decode_error='replace',
                                            strip_accents='unicode',
                                            lowercase=True,
                                            stop_words='english',
                                            ngram_range=(1, 1),
                                            dtype=np.float32,
                                            norm=None,
                                            alternate_sign=False)),
                         ('tfidf', TfidfTransformer(sublinear_tf=True))])

    transformed = pipeline.fit_transform(dataset.get_generator())

    with open(os.path.join(config.tfidf_dir, FC.VECTORIZED_PAPERS),
              'wb') as file:
        pickle.dump(transformed, file)

    with open(os.path.join(config.tfidf_dir, FC.TFIDF_PIPELINE_PAPERS),
              'wb') as file:
        pickle.dump(pipeline, file)

    with open(os.path.join(config.tfidf_dir, FC.PAPER_ID_MAP), 'wb') as file:
        pickle.dump(dataset.ids, file)


def compute_tfidf_vectorization_authors(config):
    logger.info('computing tfidf vectorization for authors')

    db_string = get_db_string(config)
    db_session, _ = create_db_session(db_string)

    dataset = AuthorsDataset(db_session)

    pipeline = Pipeline([('hashvec',
                          CountVectorizer(
                              decode_error='replace',
                              strip_accents='unicode',
                              lowercase=True,
                              stop_words='english',
                              ngram_range=(1, 1),
                              dtype=np.float32,
                          )), ('tfidf', TfidfTransformer(sublinear_tf=True))])

    transformed = pipeline.fit_transform(dataset.get_generator())

    os.makedirs(config.tfidf_dir, exist_ok=True)

    with open(os.path.join(config.tfidf_dir, FC.VECTORIZED_AUTHORS),
              'wb') as file:
        pickle.dump(transformed, file)

    with open(os.path.join(config.tfidf_dir, FC.TFIDF_PIPELINE_AUTHORS),
              'wb') as file:
        pickle.dump(pipeline, file)

    with open(os.path.join(config.tfidf_dir, FC.PAPER_ID_MAP_AUTHORS),
              'wb') as file:
        pickle.dump(dataset.ids, file)
