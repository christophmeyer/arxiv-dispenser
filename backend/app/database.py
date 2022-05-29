import os
import pickle
import hashlib
import uuid

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Table, PickleType, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import or_

from utils import (download_paper, extract_affiliations,
                   time_filter_to_unix_timestamp)
from paper_processing import convert_pdf_to_text_pkl, paper_id_to_file_name

Base = declarative_base()


def hash_password(salt, password):
    return hashlib.sha512((salt + password).encode('utf-8')).hexdigest()


favorites_table = Table('favorites', Base.metadata,
                        Column('paper_id', String, ForeignKey('papers.id')),
                        Column('user_id', String, ForeignKey('users.id')))

savedqueries_table = Table('savedqueries', Base.metadata,
                           Column('query_id', String, ForeignKey('queries.id')),
                           Column('user_id', String, ForeignKey('users.id')))

affiliations_table = Table(
    'affiliations', Base.metadata,
    Column('paper_id', String, ForeignKey('papers.id')),
    Column('organization_id', String, ForeignKey('organizations.id')))

query_affiliations_table = Table(
    'query_affiliations', Base.metadata,
    Column('query_id', String, ForeignKey('queries.id')),
    Column('organization_id', String, ForeignKey('organizations.id')))


def assemble_paper_dicts(paper_query, user_favorites=None):
    papers = []
    for paper in paper_query:
        paper_dict = paper.to_dict()
        if user_favorites is not None:
            if paper in user_favorites:
                paper_dict['favorite'] = True
            else:
                paper_dict['favorite'] = False
        else:
            paper_dict['favorite'] = None
        papers.append(paper_dict)
    return papers


def get_user(db_session, user_id):
    return db_session.query(User).filter(User.idx == user_id).first()


def get_paper(db_session, paper_id):
    return db_session.query(Paper).filter(Paper.idx == paper_id).first()


def get_query(db_session, query_id):
    return db_session.query(Query).filter(Query.idx == query_id).first()


def fulfill_get_saved_queries(db_session, user):
    #TODO: optimize this
    db_query = (db_session.query(
        savedqueries_table,
        Query).filter(savedqueries_table.c.user_id == user.idx).join(
            Query, Query.idx == savedqueries_table.c.query_id))

    saved_queries = [result._asdict()['Query'].to_dict() for result in db_query]
    return {'saved_queries': saved_queries}


def fulfill_paper_query(db_session, tfidf, config, user, tab, time_filter,
                        categories, affiliations, query_type, search_query,
                        similar_id, offset):

    filter_conditions = []

    if time_filter != None:
        try:
            cutoff = time_filter_to_unix_timestamp(time_filter)
            filter_conditions.append(Paper.created > cutoff)
        except ValueError:
            return 'Invalid time filter', 400
    else:
        cutoff = 0

    if categories != None:
        categories = categories.split(',')
        filter_conditions.append(Paper.primary_category.in_(categories))
    else:
        categories = []

    if affiliations is not None:
        affiliations = affiliations.split(',')
        filter_conditions.append(
            or_(*
                [Paper.affiliations.any(idx=org_id)
                 for org_id in affiliations]))
    else:
        affiliations = []

    if tab == 'favorites' and user is not None:
        db_query = (db_session.query(
            favorites_table,
            Paper.idx).filter(favorites_table.c.user_id == user.idx).join(
                Paper, Paper.idx == favorites_table.c.paper_id))
    else:
        db_query = paper_query = db_session.query(Paper.idx)

    if search_query is not None and similar_id is None:
        paper_filter_query = (db_query.filter(*filter_conditions).all())

        filtered_ids = [paper[0] for paper in paper_filter_query]

        sorted_ids = tfidf.search(search_query, time_filter, categories,
                                  affiliations, query_type, filtered_ids)
        paper_query = (db_query.filter(
            Paper.idx.in_(sorted_ids[offset:(
                offset +
                config.papers_per_request)])).with_entities(Paper).all())

        paper_query.sort(key=lambda paper: sorted_ids.index(paper.idx))

    elif search_query is None and similar_id is not None:
        sorted_ids = tfidf.search_similar(similar_id)
        paper_query = (db_query.filter(*filter_conditions).filter(
            Paper.idx.in_(sorted_ids[offset:(
                offset +
                config.papers_per_request)])).with_entities(Paper).all())
    else:
        paper_query = (db_query.filter(*filter_conditions).order_by(
            Paper.created.desc()).limit(
                config.papers_per_request).offset(offset).with_entities(Paper))

    if user is not None:
        user_favorites = user.favorites
    else:
        user_favorites = None
    papers = {
        'papers':
            assemble_paper_dicts(paper_query, user_favorites=user_favorites),
        'cutoff':
            cutoff
    }

    return papers


class User(Base):
    __tablename__ = 'users'
    idx = Column('id', String, primary_key=True)
    name = Column('name', String)
    pw_hash = Column('pw_hash', String)
    salt = Column('salt', String)
    favorites = relationship('Paper', secondary=favorites_table)
    saved_queries = relationship('Query', secondary=savedqueries_table)

    def __init__(self, name, password):
        self.salt = uuid.uuid4().hex
        self.idx = uuid.uuid4().hex
        self.name = name,
        self.pw_hash = hash_password(self.salt, password)

    def validate_credentials(self, name, password):
        return self.name == name and hash_password(self.salt,
                                                   password) == self.pw_hash


class Organization(Base):
    __tablename__ = 'organizations'
    idx = Column('id', String, primary_key=True)


def get_organization(db_session, organization_id):
    return db_session.query(Organization).filter(
        Organization.idx == organization_id).first()


class Query(Base):
    __tablename__ = 'queries'

    idx = Column('id', String, primary_key=True)
    description = Column('description', String)
    time = Column('time', String)
    search_string = Column('search_string', String)
    search_type = Column('search_type', String)
    categories = Column('categories', PickleType)
    affiliations = relationship('Organization',
                                secondary=query_affiliations_table)

    def to_dict(self):
        return {
            'id': self.idx,
            'description': self.description,
            'query': {
                'value': self.search_string,
                'type': self.search_type
            },
            'filters': {
                'time':
                    self.time,
                'categories':
                    self.categories,
                'affiliations': [
                    affiliation.idx for affiliation in self.affiliations
                ]
            }
        }


class Paper(Base):
    __tablename__ = 'papers'

    idx = Column('id', String, primary_key=True)
    created = Column('created', BigInteger)
    title = Column('title', String)
    abstract = Column('abstract', String)
    authors = Column('authors', PickleType)
    doi = Column('doi', String)
    journal_ref = Column('journal_ref', String)
    primary_category = Column('primary_category', PickleType)
    categories = Column('categories', PickleType)
    versions = Column('versions', PickleType)
    affiliations = relationship('Organization', secondary=affiliations_table)

    def download_full_text(self, arxiv_base_url, full_text_dir):
        id_and_version = self.idx + self.versions[-1]['version']
        pdf_filename = paper_id_to_file_name(self.to_dict())
        pdf_path = os.path.join(full_text_dir, pdf_filename)
        pickle_filename = '.'.join(pdf_filename.split('.')[:-1]) + '.pkl'
        self.full_text_file_path = os.path.join(full_text_dir, pickle_filename)

        if not os.path.exists(self.full_text_file_path):
            download_paper(arxiv_base_url, id_and_version, pdf_path)
            convert_pdf_to_text_pkl(os.path.join(full_text_dir, pdf_filename),
                                    self.full_text_file_path)
            os.remove(pdf_path)
        return self.full_text_file_path

    def extract_affiliation(self, affiliations, full_text_file_path,
                            db_session):
        with open(full_text_file_path, 'rb') as file:
            papers_txt = pickle.load(file)

        for organization_name in extract_affiliations(papers_txt[0],
                                                      affiliations):
            organization = get_organization(db_session=db_session,
                                            organization_id=organization_name)
            self.affiliations.append(organization)

    def to_dict(self):
        return {
            'id':
                self.idx,
            'created':
                self.created,
            'title':
                self.title,
            'abstract':
                self.abstract,
            'authors':
                self.authors,
            'doi':
                self.doi,
            'journal_ref':
                self.journal_ref,
            'primary_category':
                self.primary_category,
            'categories':
                self.categories,
            'versions':
                self.versions,
            'affiliations': [
                affiliation.idx for affiliation in self.affiliations
            ]
        }


def get_db_string(config):
    db_string = 'postgresql://postgres:{}@{}:{}/postgres'.format(
        config.db_password, config.db_host, config.db_port)
    return db_string


def create_db_session(db_string):
    db_engine = create_engine(db_string, echo=True)
    Session = sessionmaker(db_engine)
    return Session(), db_engine
