from flask import Flask, render_template, request, redirect, url_for, jsonify, session  # noqa
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from flask_login import LoginManager, login_required, login_user, \
    logout_user, current_user
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

from database_setup import Base, Category, Item, User
from helper import getCategories
import os
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

"""Configuration"""


class Auth:
    """Google Project Details"""
    CLIENT_ID = '747877814525-6nb508gui4o896ibppgics50v6bs7srm.apps.googleusercontent.com'  # noqa
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

# Databse connection
DBSession = sessionmaker(bind=engine)
dbsession = DBSession()

# Login initialisation
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    # checks if user signed in
    return dbsession.query(User).filter(User.id == user_id).first()


def get_google_auth(state=None, token=None):
    """
    Checks for user authentication
    """
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
    """
    Loads index page
    """
    latest_item = dbsession.query(Item).join(Category).order_by(desc(Item.id)).limit(10).all()  # noqa
    return render_template('main.html',
                           category_list=getCategories(),
                           items=latest_item)


@app.route('/catalog.json')
def view_catalog_json():
    """
    Returns whole catalog in JSON format
    """
    res_json = dict()
    res_json['category'] = []
    categories = dbsession.query(Category).all()

    for cat in categories:
        cat_dict = dict()
        cat_dict['id'] = cat.id
        cat_dict['name'] = cat.name
        cat_dict['items'] = [i.serialize for i in cat.item]
        res_json['category'].append(cat_dict)

    return jsonify(res_json)


@app.route('/categories')
def view_category_json():
    """
    Returns whole category item in JSON format
    """
    cat = dbsession.query(Category).all()
    return jsonify(categoy=[i.serialize for i in cat])


@app.route('/categories/add/')
@login_required
def add_category():
    """
    Renders category form
    """
    return render_template(
        'category_form.html',
        target_url=url_for('add_category_save'))


@app.route('/categories/add/', methods=['POST'])
@login_required
def add_category_save():
    """
    Adds category to database
    """
    form = request.form

    category = Category(name=form['name'])
    dbsession.add(category)
    dbsession.commit()
    return redirect(url_for('add_category'))


@app.route('/catalog/add/')
@login_required
def add_item():
    """
    Renders add Item form
    """
    category = dbsession.query(Category).all()
    return render_template(
        'item_form.html',
        target_url=url_for('add_item_save'),
        category_list=category,
        item=Item())


@app.route('/catalog/add/', methods=['POST'])
@login_required
def add_item_save():
    """
    Adds item to database
    """
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
    """
    Renders category items
    """
    items = dbsession.query(Item).join(Category).filter(Category.name == category).order_by(desc(Item.id)).all()  # noqa

    return render_template(
        'category.html',
        cat_items=items,
        category=category,
        category_list=getCategories())


@app.route('/catalog/<category>/<item>')
def show_item(category, item):
    """
    Renders item detail page
    """
    item = dbsession.query(Item).filter(Item.title == item).first()

    return render_template(
        'item.html', item=item, category=category)


@app.route('/catalog/<category>/<item_id>/edit')
@login_required
def edit_item(category, item_id):
    """
    Renders item edit form
    """
    category = dbsession.query(Category).all()
    item = dbsession.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_form.html',
        target_url=url_for('save_item', item_id=item_id),
        category_list=category,
        item=item)


@app.route('/catalog/<item_id>/save', methods=['POST'])
@login_required
def save_item(item_id):
    """
    Updates item details
    """
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
    """
    Renders item delete confirmation form
    """
    item = dbsession.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_delete.html',
        target_url=url_for('delete_item_commit', item_id=item_id, category=category),  # noqa
        item=item)


@app.route('/catalog/<category>/<item_id>/delete', methods=['POST'])
@login_required
def delete_item_commit(category, item_id):
    """
    Removes Item from database
    """
    dbsession.query(Item).filter(Item.id == item_id).delete()
    dbsession.commit()

    return redirect(url_for('index'))


@app.route('/login')
def login():
    """
    Redirects for login
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    # set auth details
    session['oauth_state'] = state
    # redirect to google sign in
    return redirect(auth_url)


@app.route('/gCallback')
def callback():
    """
    Google authentication Callback
    """
    # Redirects if not logged in
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    # checks for authntication error
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        google = get_google_auth(state=session['oauth_state'])
        try:
            # Fetch tonken
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        # get user info if availabale
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = dbsession.query(User).filter_by(email=email).first()
            # sets details if not avialbale
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            # Adds user to databse
            dbsession.add(User(email=user.email, token=user.token, name=user.name))  # noqa
            dbsession.commit()
            login_user(user)
            # redirects to homepage
            return redirect(url_for('index'))
        return 'Could not fetch your information.'


@app.route('/logout')
@login_required
def logout():
    """
    Sign outs user
    """
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
