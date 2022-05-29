import os
import pickle
from collections import OrderedDict
import logging

import numpy as np

from constants import FilenameConstants as FC

logger = logging.getLogger('gunicorn.error')


class TfidfSearch():

    def __init__(self, config):

        self.config = config
        self.is_initialized = False

        self.load_document_vectors()
        self.cache = Queue(max_length=config.max_queries_cache)

    def load_document_vectors(self):
        if not os.path.exists(self.config.tfidf_dir):
            logger.info(
                'tfidf_dir does not exist, setting is_initialized to False')
            self.is_initialized = False
            return

        try:
            if self.is_initialized:
                logger.info('flushing current document vectors')
                del self.transformed
                del self.pipeline
                del self.ids
                del self.transformed_authors
                del self.pipeline_authors
                del self.ids_authors

            self.is_initialized = False

            logger.info('loading new document vectors')
            with open(os.path.join(self.config.tfidf_dir, FC.VECTORIZED_PAPERS),
                      'rb') as file:
                self.transformed = pickle.load(file)

            with open(
                    os.path.join(self.config.tfidf_dir,
                                 FC.TFIDF_PIPELINE_PAPERS), 'rb') as file:
                self.pipeline = pickle.load(file)

            with open(os.path.join(self.config.tfidf_dir, FC.PAPER_ID_MAP),
                      'rb') as file:
                self.ids = pickle.load(file)

            with open(
                    os.path.join(self.config.tfidf_dir, FC.VECTORIZED_AUTHORS),
                    'rb') as file:
                self.transformed_authors = pickle.load(file)

            with open(
                    os.path.join(self.config.tfidf_dir,
                                 FC.TFIDF_PIPELINE_AUTHORS), 'rb') as file:
                self.pipeline_authors = pickle.load(file)

            with open(
                    os.path.join(self.config.tfidf_dir,
                                 FC.PAPER_ID_MAP_AUTHORS), 'rb') as file:
                self.ids_authors = np.array(pickle.load(file))

            self.id_to_pos = {self.ids[n]: n for n in range(len(self.ids))}
            self.id_to_author_pos = {}
            for n, paper_id in enumerate(self.ids_authors):
                if paper_id in self.id_to_author_pos:
                    self.id_to_author_pos[paper_id].append(n)
                else:
                    self.id_to_author_pos[paper_id] = [n]

            {self.ids_authors[n]: n for n in range(len(self.ids_authors))}

            self.is_initialized = True
        except Exception as err:
            logger.error(err, exc_info=True)
            logger.error(
                'loading of document vectors failed, setting is_initialized to False'
            )
            self.is_initialized = False

    def flush_cache(self):
        self.cache.data = OrderedDict()

    def search_similar(self, paper_id):
        if not self.is_initialized:
            return []
        if (paper_id, 'similar') in self.cache:
            return self.cache[(paper_id, 'similar')]
        else:
            try:
                paper_pos = self.ids.index(paper_id)
            except:
                return []

            paper_vector = self.transformed[paper_pos]
            scores = self.transformed.dot(paper_vector.transpose())

            sorted_scores = np.argsort(scores.todense().reshape(-1))
            sorted_ids = []
            for num in np.nditer(sorted_scores):
                if scores[num] > 0.0:
                    sorted_ids.append(self.ids[num])

            sorted_ids.reverse()
            self.cache.enqueue(((paper_id, 'similar'), sorted_ids))
            return sorted_ids

    def search(self,
               query_string,
               time_filter,
               categories,
               affiliations,
               query_type='full_text',
               filtered_ids=None):
        if not self.is_initialized or len(filtered_ids) == 0:
            return []
        cache_key = (query_string, query_type, time_filter, tuple(categories),
                     tuple(affiliations))
        if cache_key in self.cache:
            logger.info('cache key {} found in cache'.format(cache_key))
            return self.cache[cache_key]
        else:
            if query_type == 'full_text':
                return self._search_full_text(query_string, cache_key,
                                              filtered_ids)
            elif query_type == 'author':
                return self._search_author(query_string, cache_key,
                                           filtered_ids)

    def _search_author(self, query_string, cache_key, filtered_ids):

        filtered_positions = []

        for paper_id in filtered_ids:
            filtered_positions += self.id_to_author_pos[paper_id]

        filtered_positions = np.array(filtered_positions)
        query_vector = self.pipeline_authors.transform([query_string])
        scores = np.squeeze(
            np.asarray((self.transformed_authors[filtered_positions, :].dot(
                query_vector.transpose()).todense())))
        sorted_scores = np.array(np.argsort((-1) * scores))

        sorted_ids = list(self.ids_authors[filtered_positions[sorted_scores][
            scores[sorted_scores] > 0]])
        self.cache.enqueue((cache_key, sorted_ids))

        return sorted_ids

    def _search_full_text(self, query_string, cache_key, filtered_ids):
        filtered_positions = [
            self.id_to_pos[paper_id] for paper_id in filtered_ids
        ]
        query_vector = self.pipeline.transform([query_string])
        scores = self.transformed[filtered_positions, :].dot(
            query_vector.transpose())
        sorted_scores = np.argsort((-1) * scores.todense().reshape(-1))
        sorted_ids = []

        for num in np.nditer(sorted_scores):
            if scores[num] > 0.0:
                sorted_ids.append(self.ids[filtered_positions[num]])
            if len(sorted_ids) == self.config.max_search_results:
                break

        self.cache.enqueue((cache_key, sorted_ids))
        return sorted_ids


class Queue:

    def __init__(self, max_length):
        self.data = OrderedDict()
        self.max_length = max_length

    def enqueue(self, item):
        key, value = item
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        while len(self.data) > self.max_length:
            self.dequeue()

    def dequeue(self):
        try:
            return self.data.popitem(last=False)
        except KeyError:
            logger.error("Empty queue")

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data)
