import os
import uuid
import logging

from flask import Flask, session, g, request

from database import (Query, User, Organization, create_db_session,
                      fulfill_paper_query, get_db_string,
                      fulfill_get_saved_queries, get_organization, get_query,
                      get_user, get_paper)
from utils import Config
from fetch_papers import initialize_tables
from search import TfidfSearch

app = Flask(__name__)
config = Config(os.getenv('CONFIG_PATH'))
app.secret_key = config.secret_key
tfidf = TfidfSearch(config)

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# initialize db tables if necessary
initialize_tables(config)


@app.before_request
def before_request():
    db_string = get_db_string(config)
    db_session, db_engine = create_db_session(db_string)
    g.db_session = db_session
    g.db_engine = db_engine

    if 'user_id' in session:
        g.user = get_user(db_session=g.db_session, user_id=session['user_id'])
    else:
        g.user = None


@app.teardown_request
def close_db_connection(exception):
    g.db_session.close()


@app.route('/admin/flush', methods=['POST'])
def flush_tfidf_cache():
    tfidf.load_document_vectors()
    tfidf.flush_cache()

    return 'OK', 200


@app.route('/api/categories', methods=['GET'])
def get_categories():
    return {'categories': config.categories}


@app.route('/api/organizations', methods=['GET'])
def get_affiliations():
    db_session = g.db_session
    organization_names = [
        org.idx for org in db_session.query(Organization).all()
    ]
    return {'organizations': organization_names}


@app.route('/api/papers')
def get_papers():
    return fulfill_paper_query(
        db_session=g.db_session,
        tfidf=tfidf,
        config=config,
        user=g.user,
        tab=request.args.get('tab', 'all'),
        time_filter=request.args.get('time', None),
        categories=request.args.get('categories', None),
        affiliations=request.args.get('affiliations', None),
        query_type=request.args.get('query_type', 'full_text'),
        search_query=request.args.get('query', None),
        similar_id=request.args.get('similar_id', None),
        offset=int(request.args.get('offset', 0)))


@app.route('/api/saved', methods=['GET'])
def get_saved_queries():
    return fulfill_get_saved_queries(db_session=g.db_session, user=g.user)


@app.route('/api/saved', methods=['POST'])
def post_saved_query():

    if g.user is None:
        return 'Not logged in', 403

    query = Query(idx=str(uuid.uuid4()),
                  description=request.json['description'],
                  time=request.json['time'],
                  search_string=request.json['search_string'],
                  search_type=request.json['search_type'],
                  categories=request.json['categories'],
                  affiliations=[
                      get_organization(g.db_session, org_name)
                      for org_name in request.json['affiliations']
                  ])
    g.user.saved_queries.append(query)
    g.db_session.add(g.user)
    g.db_session.commit()
    return 'Query added', 200


@app.route('/api/saved', methods=['DELETE'])
def delete_saved_query():
    if g.user is None:
        return 'Not logged in', 403

    query = get_query(db_session=g.db_session,
                      query_id=request.json.get('query_id'))
    if query is None:
        return 'Query does not exist', 400

    if query in g.user.saved_queries:
        g.user.saved_queries.remove(query)
        g.db_session.add(g.user)
        g.db_session.commit()
        return 'Query removed', 200
    else:
        return 'Query does not exist', 400


@app.route('/api/users', methods=['POST'])
def add_new_user():
    session = g.db_session
    if session.query(User).filter(
            User.name == request.json.get('name')).count() == 0:
        session.add(
            User(name=request.json.get('name'),
                 password=request.json.get('password')))
        session.commit()
        return 'user created'
    else:
        return 'user name already exists', 409


@app.route('/api/login', methods=['POST'])
def login():
    user = g.db_session.query(User).filter(
        User.name == request.json.get('name')).first()

    if user is None:
        return 'Incorrect credentials', 403
    else:
        is_validated = user.validate_credentials(
            name=request.json.get('name'),
            password=request.json.get('password'))
        if is_validated:
            session.clear()
            session['user_id'] = user.idx
            session.modified = True
            return 'OK', 200
        else:
            return 'Incorrect credentials', 403


@app.route('/api/logincheck', methods=['GET'])
def logincheck():
    if g.user is None:
        return {'logged_in': False}, 200
    else:
        return {'logged_in': True, 'user': g.user.name}, 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return 'OK', 200


@app.route('/api/users/favorites', methods=['POST'])
def add_favorite():
    if g.user is None:
        return 'Not logged in', 403

    paper = get_paper(db_session=g.db_session,
                      paper_id=request.json.get('paper_id'))
    if paper is None:
        return 'paper_id does not exist', 400

    if paper in g.user.favorites:
        return 'Paper already in favorites', 200
    else:
        g.user.favorites.append(paper)
        g.db_session.add(g.user)
        g.db_session.commit()
        return 'Favorite added', 200


@app.route('/api/users/favorites', methods=['DELETE'])
def remove_favorite():
    if g.user is None:
        return 'Not logged in', 403

    paper = get_paper(db_session=g.db_session,
                      paper_id=request.json.get('paper_id'))
    if paper is None:
        return 'paper_id does not exist', 400

    if paper in g.user.favorites:
        g.user.favorites.remove(paper)
        g.db_session.add(g.user)
        g.db_session.commit()
        return 'Favorite removed', 200
    else:
        return 'Paper is not a favorite', 200


if __name__ == "__main__":
    app.run()
