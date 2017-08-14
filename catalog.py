from flask import Flask,render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine,desc
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User
from helper import getCategories

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.errorhandler(404)
def page_not_found(error):
    return 'Error:404. Sorry! This page does not exist', 404


@app.route('/')
def index():
    latest_item = session.query(Item).join(Category).order_by(desc(Item.id)).limit(10).all()
    return render_template('main.html', category_list=getCategories(), items=latest_item)


@app.route('/categories')
def view_category_json():
    cat = session.query(Category).all()
    return jsonify(categoy=[i.serialize for i in cat])


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


@app.route('/catalog')
def view_catalog_json():
    item_obj = session.query(Item).all()
    return jsonify(item=[i.serialize for i in item_obj])


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
        cat_id=form['cat_id'])
    session.add(item)
    session.commit()
    return redirect(url_for('index'))


@app.route('/catalog/<category>/')
def show_category(category):

    items = session.query(Item).join(Category).filter(Category.name == category).order_by(desc(Item.id)).all()

    return render_template(
        'category.html', cat_items=items, category=category, category_list=getCategories(),)


@app.route('/catalog/<category>/<item>')
def show_item(category,item):

    item = session.query(Item).filter(Item.title == item).first()

    return render_template(
        'item.html', item=item, category=category)


@app.route('/catalog/<category>/<item_id>/edit')
def edit_item(category ,item_id):
    category = session.query(Category).all()
    item = session.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_form.html',
        target_url=url_for('save_item',item_id=item_id), category_list=category, item=item)


@app.route('/catalog/<item_id>/save', methods=['POST'])
def save_item(item_id):

    form = request.form
    item = session.query(Item).filter(Item.id == item_id).first()

    item.title = form['title']
    item.description = form['desc']
    item.cat_id = form['cat_id']

    session.add(item)
    session.commit()

    return redirect(url_for('index'))


@app.route('/catalog/<category>/<item_id>/delete')
def delete_item(category ,item_id):
    item = session.query(Item).filter(Item.id == item_id).first()

    return render_template(
        'item_delete.html',
        target_url=url_for('delete_item_commit', item_id=item_id,category=category),
        item=item)


@app.route('/catalog/<category>/<item_id>/delete', methods=['POST'])
def delete_item_commit(category, item_id):
    session.query(Item).filter(Item.id == item_id).delete()
    session.commit()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
