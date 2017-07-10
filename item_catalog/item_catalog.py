from flask import Flask, render_template, request, redirect, jsonify, url_for, session, g
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from functools import wraps



from apiclient import discovery
import httplib2
from oauth2client import client, crypt

from database_setup import Base, Item, Category, User

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
db_session = DBsession()


app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='whatwhat'
))


def clear_DB():
	users = db_session.query(User).all()
	categories = db_session.query(Category).all()
	items = db_session.query(Item).all()
	for user in users:
		db_session.delete(user)
	for item in items:
		db_session.delete(item)
	for c in categories:
		db_session.delete(c)
	db_session.commit()

def is_users_item(item_id, user_id):
	"""Check if item belongs to user.

	Returns:
		True if item was created by user. False otherwise.
	"""
	item = db_session.query(Item).filter_by(id=item_id).one()
	if item.user_id == user_id:
		return True
	else:
		return False

def google_user_exists(gid):
	if db_session.query(User).filter_by(gid=gid).count() == 0:
		return False
	else:
		return True

def only_signed_in(route_function):
	"""Decorator function to redirect if there is no user logged in.

	Args:
		route_function (function): The routing function to decorate.

	Returns:
		function: Function that redirects to the login page if no user is signed in.

	Example:
		>>> @app.route('/path')
		... @only_logged_in
		... def secret_site():
		... 	return 'Secret'
	"""
	@wraps(route_function)
	def new_route_function(*a, **kw):
		if 'user_id' in session:
			return route_function(*a, **kw)
		else:
			return redirect(url_for('credentials'))
	return new_route_function

@app.route('/')
def show_all_items():
	categories = db_session.query(Category).all()
	items = db_session.query(Item).all()
	return render_template(
		'all-items.html',
		categories=categories,
		items=items)

@app.route('/JSON')
def show_all_items_JSON():
	items = db_session.query(Item).all()
	return jsonify(Items=[i.serialize for i in items])

@app.route('/category/<int:category_id>')
def show_category_items(category_id):
	try:
		category = db_session.query(Category)\
			.filter_by(id=category_id).one()
	except:
		return "This Category Does Not Exist"
	categories = db_session.query(Category)\
		.order_by(asc(Category.name)).all()
	items = db_session.query(Item)\
		.filter_by(category_id=category_id).order_by(asc(Item.name)).all()

	return render_template(
		'category.html',
		items=items,
		categories=categories,
		category_name=category.name)

@app.route('/category/<int:category_id>/JSON')
def show_category_items_JSON(category_id):
	items = db_session.query(Item)\
		.filter_by(category_id=category_id).order_by(asc(Item.name)).all()
	return jsonify(Items=[i.serialize for i in items])

@app.route('/category/JSON')
def show_categories_JSON():
	categories = db_session.query(Category).all()
	return jsonify(Categories=[c.serialize for c in categories])


@app.route('/item/<int:item_id>')
def show_single_item(item_id):
	item = db_session.query(Item).filter_by(id=item_id).one()
	item_category = db_session.query(Category).filter_by(id=item.category_id).one()
	return render_template(
		'show-item.html',
		item=item,
		item_category=item_category.name)

@app.route('/item/<int:item_id>/JSON')
def show_single_item_JSON(item_id):
	item = db_session.query(Item).filter_by(id=item_id).one()
	return jsonify(Item=item.serialize)

@app.route('/add', methods=['GET','POST'])
@only_signed_in
def add_item():
	if request.method == 'POST':
		if not (request.form['name'] and request.form['description'] and \
			request.form['category']):
			return render_template(
				'add-item.html',
				error='You must fill out all fields!')

		new_category = request.form['category'].capitalize()
		if db_session.query(Category).filter_by(name=new_category).count() == 0:
			category = Category(name=new_category)
		else:
			category = db_session.query(Category).filter_by(name=new_category).one()


		new_item = Item(
			name=request.form['name'],
			description=request.form['description'],
			category=category,
			date_created=datetime.now(),
			date_updated=datetime.now(),
			user_id=session['user_id'])
		db_session.add(new_item)
		db_session.commit()
		return redirect('/')

	else:
		return render_template('add-item.html')

@app.route('/item/<int:item_id>/edit', methods=['GET','POST'])
@only_signed_in
def edit_item(item_id):
	item = db_session.query(Item).filter_by(id=item_id).one()
	category = db_session.query(Category).filter_by(id=item.category_id).one()
	if is_users_item(item.id, session['user_id']):
		if request.method == 'POST':
			if not (request.form['name'] and request.form['description'] and \
				request.form['category']):
				return render_template(
					'edit-item.html',
					item=item,
					category=category.name,
					error='You must fill out all fields!')
			item.name = request.form['name']
			item.description = request.form['description']
			item.date_updated = datetime.now()
			new_category_name = request.form['category']
			if new_category_name != category.name:
				if db_session.query(Category).filter_by(name=new_category_name).count() == 0:
					new_category = Category(name=new_category_name)
				else:
					new_category = db_session.query(Category)\
						.filter_by(name=new_category_name).one()

				is_last_of_category = db_session.query(Item)\
					.filter_by(category_id=item.category_id).count() == 1
				if is_last_of_category:
					db_session.delete(category)
				item.category = new_category
			db_session.commit()
			return redirect('/item/%s' % item_id)
	else:
		return redirect(url_for('credentials'))
	return render_template(
		'edit-item.html',
		item=item,
		category=category.name,
		error='')

@app.route('/item/<int:item_id>/delete',methods=['GET','POST'])
@only_signed_in
def delete_item(item_id):
	item = db_session.query(Item).filter_by(id=item_id).one()
	if is_users_item(item.id, session['user_id']):
		if request.method == 'POST':
			is_last_of_category = db_session.query(Item)\
				.filter_by(category_id=item.category_id).count() == 1
			if is_last_of_category:
				db_session.delete(
					db_session.query(Category)\
						.filter_by(id=item.category_id).one())
			db_session.delete(item)
			db_session.commit()
			return redirect('/')
	else:
		return redirect(url_for('credentials'))
	return render_template('delete-item.html', item=item)

@app.route('/gconnect', methods=['POST'])
def google_sign_in():
	token = request.form['idtoken']
	try:
		idinfo = client.verify_id_token(
			token,
			'74998840507-ofm1jmee38bf6h08154bg4a6q2dqgkm9.apps.googleusercontent.com')

		if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
		    raise crypt.AppIdentityError("Wrong issuer.")

	except crypt.AppIdentityError:
		return 'invalid token'

	user_gid = idinfo['sub']
	name = idinfo['name']
	if not google_user_exists(user_gid):
		user = User(
			gid=user_gid,
			name=name
			)
		db_session.add(user)
		db_session.commit()
	else:
		user = db_session.query(User).filter_by(gid=user_gid).one()

	session['user_name'] = user.name
	session['user_gid'] = user_gid
	session['user_id'] = user.id


	return redirect(url_for('show_all_items'))


@app.route('/gdisconnect')
def google_sign_out():
	session.pop('user_id', None)
	session.pop('user_gid', None)
	session.pop('user_name', None)
	session.pop('user_db_object', None)
	return redirect(url_for('show_all_items'))

@app.route('/credentials')
def credentials():
	return render_template('credentials.html')

@app.route('/allusers')
def show_all_users():
	users = db_session.query(User).all()
	return jsonify(Users=[user.serialize for user in users])

