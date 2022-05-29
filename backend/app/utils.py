import requests
import os
import time
import datetime
import logging

import yaml
import pytz
from fuzzysearch import find_near_matches

logger = logging.getLogger(__name__)


def get_last_release_timestamp(now_utc):
    arxiv_release_hour_utc = 1
    release_today = datetime.datetime(year=now_utc.year,
                                      month=now_utc.month,
                                      day=now_utc.day,
                                      hour=arxiv_release_hour_utc,
                                      tzinfo=pytz.utc)

    if now_utc.isoweekday() == 6:
        return release_today - datetime.timedelta(days=1)
    elif now_utc.isoweekday() == 7:
        return release_today - datetime.timedelta(days=2)
    else:
        if now_utc > release_today:
            return release_today
        else:
            if now_utc.isoweekday() == 1:
                return release_today - datetime.timedelta(days=3)
            else:
                return release_today - datetime.timedelta(days=1)


def get_begin_submission_period(release_utc):
    arxiv_submission_deadline_hour_utc = 19
    submission_start_release_day = datetime.datetime(
        year=release_utc.year,
        month=release_utc.month,
        day=release_utc.day,
        hour=arxiv_submission_deadline_hour_utc,
        tzinfo=pytz.utc)

    if release_utc.isoweekday() in [6, 7]:
        logger.info('There is no release on the weekend')
        return False
    elif release_utc.isoweekday() in [1, 2]:
        return submission_start_release_day - datetime.timedelta(days=4)
    else:
        return submission_start_release_day - datetime.timedelta(days=2)


def get_last_submission_period_start(now_utc):
    last_release = get_last_release_timestamp(now_utc)
    return get_begin_submission_period(last_release)


def time_filter_to_unix_timestamp(filter_string):
    now = datetime.datetime.now(pytz.utc)

    if filter_string == 'last_day':
        submission_period_start = get_last_submission_period_start(now)
    elif filter_string == 'last_three_days':
        submission_period_start = get_last_submission_period_start(
            now - datetime.timedelta(days=3))
    elif filter_string == 'last_week':
        submission_period_start = get_last_submission_period_start(
            now - datetime.timedelta(days=7))
    elif filter_string == 'last_four_weeks':
        submission_period_start = get_last_submission_period_start(
            now - datetime.timedelta(days=28))
    elif filter_string == 'last_six_months':
        submission_period_start = get_last_submission_period_start(
            now - datetime.timedelta(days=183))
    elif filter_string == 'last_year':
        submission_period_start = get_last_submission_period_start(
            now - datetime.timedelta(days=365))
    elif filter_string == 'all_time':
        return 0
    else:
        raise ValueError('Unknown time filter')

    return int(submission_period_start.timestamp())


class Config:

    def __init__(self, config_path):
        with open(config_path) as file:
            config = yaml.load(file, yaml.FullLoader)
        self.__dict__.update(config)


def download_papers(arxiv_base_url, paper_ids, paper_dir):
    for paper_id in paper_ids:
        if not os.path.exists(os.path.join(paper_dir, paper_id + '.pdf')):
            download_paper(arxiv_base_url, paper_id, paper_dir)


def download_paper(arxiv_base_url, paper_id, pdf_path):
    pdf_url = arxiv_base_url + '/pdf/' + paper_id + '.pdf'

    is_downloaded = False
    while not is_downloaded:
        try:
            resp = requests.get(pdf_url)
            is_downloaded = True
        except:
            time.sleep(10)

    with open(pdf_path, 'wb') as file:
        file.write(resp.content)
    logger.info('downloaded {}'.format(pdf_url))


def extract_affiliations(front_page, affiliations):
    found_affiliations = []
    for affiliation in affiliations:
        if check_affiliation(front_page, affiliation):
            found_affiliations.append(affiliation['name'])
    return found_affiliations


def check_affiliation(front_page, affiliation):
    for pattern in affiliation['patterns']:
        matches = find_near_matches(pattern['text'],
                                    front_page,
                                    max_l_dist=pattern['max_l_dist'])
        if len(matches) > 0:
            return True
    return False
