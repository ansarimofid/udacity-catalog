from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user, UserMixin
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

from database_setup import Base, Category, Item, User
from helper import getCategories
import os
import json

# basedir = os.path.abspath(os.path.dirname(__file__))
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

"""Configuration"""


class Auth:
    """Google Project Credentials"""
    CLIENT_ID = ('747877814525-6nb508gui4o896ibppgics50v6bs7srm.apps.googleusercontent.com')
    CLIENT_SECRET = 'pvMBKkrRR7OU7Hj_5S6S9uMN'
    REDIRECT_URI = 'http://127.0.0.1:5000/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']


class Config:
    """Base config"""
    APP_NAME = "catalog-app"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"


"""initialisation"""
app = Flask(__name__)
app.secret_key = "super secret key"
# app.config.from_object(config['dev'])
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
dbsession = DBSession()

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    return dbsession.query(User).filter(User.id == user_id).first()


def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth


@app.errorhandler(404)
def page_not_found(error):
    return 'Error:404. Sorry! This page does not exist', 404


@app.route('/')
def index():
    latest_item = dbsession.query(Item).join(Category).order_by(desc(Item.id)).limit(10).all()
    return render_template('main.html', category_list=getCategories(), items=latest_item)


@app.route('/catalog.json')
def view_catalog_json():
    res_json = {}
    res_json['category'] = []
    categories = dbsession.query(Category).all()

    for cat in categories:
        catDict = {}
        catDict['id'] = cat.id
        catDict['name'] = cat.name
        catDict['items'] = [i.serialize for i in cat.item]
        res_json['category'].append(catDict)

    return jsonify(res_json)


@app.route('/categories')
def view_category_json():
    cat = dbsession.query(Category).all()
    return jsonify(categoy=[i.serialize for i in cat])


@app.route('/categories/add/')
@login_required
def add_category():
    return render_template(
        'category_form.html',
        target_url=url_for('add_category_save'))


@app.route('/categories/add/', methods=['POST'])
@login_required
def add_category_save():
    form = request.form

    category = Category(name=form['name'])
    dbsession.add(category)
    dbsession.commit()
    return redirect(url_for('add_category'))


@app.route('/catalog/add/')
@login_required
def add_item():
    category = dbsession.query(Category).all()
    return render_template(
        'item_form.html',
        target_url=url_for('add_item_save'), category_list=category, item=Item())


@app.route('/catalog/add/', methods=['POST'])
@login_required
def add_item_save():
    form = request.form

    item = Item(
        title=form['title'],
        description=form['desc'],
        cat_id=form['cat_id'],
        user_id=current_user.id)
    dbsession.add(item)
    dbsession.commit()
    return redirect(url_for('index'))


@app.route('/catalog/<category>/')
def show_category(category):
    items = dbsession.query(Item).join(Category).filter(Category.name == category).order_by(desc(Item.id)).all()

    return render_template(
        'category.html', cat_items=items, category=category, category_list=getCategories(), )


@app.route('/catalog/<category>/<item>')
def show_item(category, item):
    item = dbsession.query(Item).filter(Item.title == item).first()

    return render_template(
        'item.html', item=item, category=category)


@app.route('/catalog/<category>/<item_id>/edit')
@login_required
def edit_item(category, item_id):
    category = dbsession.query(Category).all()
    item = dbsession.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_form.html',
        target_url=url_for('save_item', item_id=item_id), category_list=category, item=item)


@app.route('/catalog/<item_id>/save', methods=['POST'])
@login_required
def save_item(item_id):
    form = request.form
    item = dbsession.query(Item).filter(Item.id == item_id).first()

    item.title = form['title']
    item.description = form['desc']
    item.cat_id = form['cat_id']

    dbsession.add(item)
    dbsession.commit()

    return redirect(url_for('index'))


@app.route('/catalog/<category>/<item_id>/delete')
@login_required
def delete_item(category, item_id):
    item = dbsession.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_delete.html',
        target_url=url_for('delete_item_commit', item_id=item_id, category=category),
        item=item)


@app.route('/catalog/<category>/<item_id>/delete', methods=['POST'])
@login_required
def delete_item_commit(category, item_id):
    dbsession.query(Item).filter(Item.id == item_id).delete()
    dbsession.commit()

    return redirect(url_for('index'))


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/gCallback')
def callback():
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = dbsession.query(User).filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)

            dbsession.add(User(email=user.email, token=user.token, name=user.name))
            dbsession.commit()
            login_user(user)
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
