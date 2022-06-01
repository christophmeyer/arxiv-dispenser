import os
import requests
import datetime
import time
import yaml
import pickle
import logging

import pytz
import feedparser
from sqlalchemy import exc

from database import Base, Paper, Organization, create_db_session, get_db_string
from utils import time_filter_to_unix_timestamp

logger = logging.getLogger(__name__)


def convert_metadata_to_paper(metadata_dict):
    paper = Paper(idx=metadata_dict['id'],
                  created=metadata_dict['created'].timestamp(),
                  title=metadata_dict['title'],
                  abstract=metadata_dict['abstract'],
                  authors=metadata_dict['authors'],
                  doi=metadata_dict['doi'],
                  journal_ref=metadata_dict['journal-ref'],
                  primary_category=metadata_dict['primary_category'],
                  categories=metadata_dict['categories'],
                  versions=metadata_dict['versions'])
    return paper


def update_database_with_last_days_papers(db_session, arxiv_base_url,
                                          interesting_categories, affiliations,
                                          save_metadata_dir,
                                          save_full_text_dir):

    timestamp_last_period = datetime.datetime.fromtimestamp(
        time_filter_to_unix_timestamp('last_day'), tz=pytz.utc)

    papers = fetch_recent_papers(categories=interesting_categories,
                                 cutoff_timestamp=timestamp_last_period,
                                 arxiv_base_url=arxiv_base_url,
                                 affiliations=affiliations,
                                 save_metadata_dir=save_metadata_dir,
                                 save_full_text_dir=save_full_text_dir,
                                 db_session=db_session)

    paper_idx = 0
    for current_paper in papers:
        try:
            existing_entry = db_session.query(Paper).filter(
                Paper.idx == current_paper.idx).first()
        except exc.SQLAlchemyError as e:
            logger.error(e, exc_info=True)
            time.sleep(10)
            continue

        if existing_entry:
            existing_entry = current_paper
            logger.info('{} already in database'.format(current_paper.idx))
        else:
            db_session.add(current_paper)
        paper_idx += 1
    db_session.commit()
    logger.info('Done downloading papers.')


def clean_title(title):
    return title.replace('\n', ' ').replace('   ', ' ').replace('  ', ' ')


def call_arxiv_api(arxiv_base_url,
                   search_query,
                   start,
                   max_results,
                   id_list=None,
                   sort_by=None,
                   sort_order=None):

    assert (sort_order in ['ascending', 'descending', None])
    assert (sort_by in ['relevance', 'lastUpdatedDate', 'submittedDate', None])

    parameters = {
        'search_query': search_query,
        'start': str(start),
        'max_results': str(max_results)
    }

    if id_list is not None:
        parameters['id_list'] = id_list
    if sort_by is not None:
        parameters['sortBy'] = sort_by
    if sort_order is not None:
        parameters['sortOrder'] = sort_order

    return requests.post(arxiv_base_url + '/api/query?', data=parameters)


def convert_timestamps_to_datetime(entries):
    for entry in entries:
        entry['published'] = datetime.datetime.strptime(
            entry['published'] + '+0000',
            '%Y-%m-%dT%H:%M:%SZ%z').astimezone(pytz.utc)
        entry['updated'] = datetime.datetime.strptime(
            entry['updated'] + '+0000',
            '%Y-%m-%dT%H:%M:%SZ%z').astimezone(pytz.utc)


def convert_feedparser(feedparser_dict):
    converted = {}
    converted['id'] = feedparser_dict['id'].split('/')[-1].split('v')[0]
    converted['created'] = feedparser_dict['updated']
    converted['title'] = feedparser_dict['title']
    converted['abstract'] = feedparser_dict['summary']
    converted['authors'] = feedparser_dict['authors']
    converted['journal-ref'] = feedparser_dict.get('arxiv_journal_ref', '')
    converted['doi'] = feedparser_dict.get('arxiv_doi', '')
    converted['categories'] = [
        feedparser_dict['arxiv_primary_category']['term']
    ] + [x['term'] for x in feedparser_dict['tags']]
    converted['primary_category'] = converted['categories'][0]
    converted['versions'] = [{
        'version': 'v' + feedparser_dict['id'].split('/')[-1].split('v')[1],
        'created': converted['created']
    }]
    return converted


def fetch_recent_papers(categories,
                        cutoff_timestamp,
                        arxiv_base_url,
                        affiliations=None,
                        save_metadata_dir=None,
                        save_full_text_dir=None,
                        sleep_between_requests=0,
                        verbose=False,
                        db_session=None):
    metadata_dicts = []
    papers = []
    n_batch = 1

    logger.info('fetching all papers since {}'.format(cutoff_timestamp))
    while True:
        if verbose:
            logger.info('Requesting batch {}'.format(n_batch))
        search_query = 'cat:' + ' OR cat:'.join(categories)
        result = call_arxiv_api(arxiv_base_url=arxiv_base_url,
                                search_query=search_query,
                                start=(n_batch - 1) * 100,
                                max_results=100,
                                sort_by='submittedDate',
                                sort_order='descending')
        parsed_feed = feedparser.parse(result.text)

        # Check if a complete batch was returned else wait and try again
        if len(parsed_feed['entries']) == 100:
            n_batch += 1
        else:
            logger.info(
                'Did not receive full batch. Rate limited? Status {}'.format(
                    result.status_code))
            time.sleep(sleep_between_requests)
            continue

        # Convert to metadata dictionary
        convert_timestamps_to_datetime(parsed_feed['entries'])
        new_metadata_dicts = [
            convert_feedparser(entry)
            for entry in parsed_feed['entries']
            if entry['published'] > cutoff_timestamp
        ]
        metadata_dicts += new_metadata_dicts

        # Save as pickle if save_metadata_dir is given
        if save_metadata_dir is not None:
            os.makedirs(save_metadata_dir, exist_ok=True)
            for entry in new_metadata_dicts:
                with open(
                        os.path.join(save_metadata_dir,
                                     entry['id'].split('/')[-1] + '.pkl'),
                        'wb') as file:
                    pickle.dump(entry, file)

        # Break and return if cutoff reached
        if parsed_feed['entries'][-1]['published'] < cutoff_timestamp:
            break

        if verbose:
            logger.info('Current batch last timestamp {} and length {}'.format(
                parsed_feed['entries'][-1]['published'],
                len(parsed_feed['entries'])))

        # Break and return if cutoff reached
        if parsed_feed['entries'][-1]['published'] < cutoff_timestamp:
            break

        # Sleep between requests
        time.sleep(sleep_between_requests)

    logger.info('done fetching metadata.')

    # Convert metadata to Paper instances
    papers = [
        convert_metadata_to_paper(metadata_dict)
        for metadata_dict in metadata_dicts
    ]

    if save_full_text_dir is not None:
        # Download and save full text and extract affiliations
        os.makedirs(save_full_text_dir, exist_ok=True)
        logger.info('Downloading {} papers.'.format(len(papers)))
        for paper in papers:
            full_text_file_path = paper.download_full_text(
                arxiv_base_url, save_full_text_dir)
            paper.extract_affiliation(affiliations, full_text_file_path,
                                      db_session)

    return papers


def add_organization_to_database(db_session, organization):
    try:
        existing_entry = db_session.query(Organization).filter(
            Organization.idx == organization.idx).first()
    except exc.SQLAlchemyError as e:
        logger.error(e, exc_info=True)
        time.sleep(10)
        return

    if existing_entry:
        existing_entry = organization
        logger.info('{} already in database'.format(organization.idx))
    else:
        db_session.add(organization)
        db_session.commit()


def initialize_tables(config):
    db_string = get_db_string(config)
    db_session, db_engine = create_db_session(db_string)
    tables_created = False
    while not tables_created:
        try:
            Base.metadata.create_all(db_engine)
            tables_created = True
        except Exception as e:
            time.sleep(10)

    with open(config.affiliations_path) as file:
        affiliations = yaml.load(file, yaml.FullLoader)

    for organization in affiliations:
        add_organization_to_database(db_session,
                                     Organization(idx=organization['name']))
    return


def fetch_papers(config):
    db_string = get_db_string(config)
    session, _ = create_db_session(db_string)

    with open(config.affiliations_path) as file:
        affiliations = yaml.load(file, yaml.FullLoader)

    initialize_tables(config)
    update_database_with_last_days_papers(
        db_session=session,
        arxiv_base_url=config.arxiv_base_url,
        interesting_categories=config.categories,
        affiliations=affiliations,
        save_metadata_dir=config.metadata_dir,
        save_full_text_dir=config.full_text_dir)
