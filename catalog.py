from flask import Flask,render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User
from helper import getCategories

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
def hello_world():
    category = session.query(Category).all()
    return render_template('main.html', category_list=getCategories())

@app.route('/categories')
def view_category_json():
    cat = session.query(Category).all()
    return jsonify(categoy = [i.serialize for i in cat])


@app.route('/categories/add/')
def add_category():
    return render_template(
        'category_form.html',
        target_url=url_for('add_category_save'))


@app.route('/categories/add/', methods=['POST'])
def add_category_save():
    form = request.form

    category = Category(name=form['name'])
    session.add(category)
    session.commit()
    return redirect(url_for('add_category'))


@app.route('/catalog/add/')
def add_item():
    category = session.query(Category).all()
    return render_template(
        'item_form.html',
        target_url=url_for('add_item_save'), category_list=category, item=Item())


@app.route('/catalog/add/', methods=['POST'])
def add_item_save():
    form = request.form

    item = Item(
        title=form['title'],
        description=form['desc'],
        cat_id=form['title'],)
    session.add(item)
    session.commit()
    return redirect(url_for('add_item'))


if __name__ == '__main__':
    app.run()
