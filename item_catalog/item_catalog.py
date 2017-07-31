from flask import Flask, render_template, request, redirect, jsonify,\
	 url_for, session, g, send_from_directory, send_file, Response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from PIL import Image
from google.cloud import storage
import os
import io
import StringIO as StringIO
import random



from apiclient import discovery
import httplib2
from oauth2client import client, crypt

from database import init_db, db_session
from models import Item, Category, User, Photo

UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
init_db()


app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='whatwhat',
    UPLOAD_FOLER=UPLOAD_FOLDER
))

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
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


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

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
			request.form['category'] and request.form['price']):
			return render_template(
				'add-item.html',
				error='You must fill out all fields!')

		try:
			float(request.form['price'])
		except ValueError:
			return render_template(
				'add-item.html',
				error='Price is not valid!')
		new_category = request.form['category'].capitalize()
		if db_session.query(Category).filter_by(name=new_category).count() == 0:
			category = Category(name=new_category)
		else:
			category = db_session.query(Category).filter_by(name=new_category).one()


		new_item = Item(
			name=request.form['name'],
			price=round(float(request.form['price']), 2),
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
					photos=item.photos,
					error='You must fill out all fields!')
			item.name = request.form['name']
			try:
				item.price = round(float(request.form['price']), 2)
			except ValueError:
				return render_template(
					'edit-item.html',
					item=item,
					category=category.name,
					photos=item.photos,
					error='Price you entered is not Valid!')
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
		photos=item.photos,
		error='')

@app.route('/item/<int:item_id>/delete',methods=['GET','POST'])
@only_signed_in
def delete_item(item_id):
	try:
		item = db_session.query(Item).filter_by(id=item_id).one()
	except:
		return 'Not a valid item'		
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

@app.route('/item/<int:item_id>/upload_photo', methods=['POST'])
@only_signed_in
def upload_file(item_id):
	size = (300, 300)
	try:
		item = db_session.query(Item).filter_by(id=item_id).one()
	except:
		return 'Not a valid item'
	if not is_users_item(item_id, session['user_id']):
		return url_for('credentials')
	if request.method == 'POST':
		if 'file' not in request.files:
			return redirect(request.url)
		file = request.files['file']

		if file.filename == '':
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = '%s_%s.jpg' % (item.id, random.randint(1,1000000000000))
			item = db_session.query(Item).filter_by(id=item_id).one()

			# Perform image resizing
			image = Image.open(file)
			image.thumbnail(size)

			# Connect to storage bucket
			gcs = storage.Client()
			bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
			blob = bucket.blob(filename)
			
			# Upload File to Google cloud storage
			with io.BytesIO() as resized_image:	
				image.save(resized_image, format='JPEG', progressive=True)
				resized_image.seek(0)				
				blob.upload_from_file(
					resized_image,
					content_type='image/jpeg')

			
			#Add Photo to database
			item.photos.append(
				Photo(
					filename=filename,
					public_url=blob.public_url)
					)

			db_session.commit()
			return redirect(
				url_for('edit_item', item_id=item_id))

@app.route('/item/<int:item_id>/delete_photo/<int:photo_id>', methods=['POST'])
@only_signed_in
def delete_photo(item_id, photo_id):
	try:
		item = db_session.query(Item).filter_by(id=item_id).one()
		photo = db_session.query(Photo).filter_by(id=photo_id).one()
	except:
		return 'Not a valid item or photo'
	if not is_users_item(item_id, session['user_id']):
		return url_for('credentials')
	# Delete photo from file
	sc = storage.Client()
	bucket = sc.get_bucket(CLOUD_STORAGE_BUCKET)
	blob = bucket.blob(photo.filename)
	blob.delete()
	# Delete photo from database
	db_session.delete(photo)
	db_session.commit()


	return redirect(url_for('edit_item', item_id=item_id))




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
	return redirect(url_for('show_all_items'))

@app.route('/credentials')
def credentials():
	return render_template('credentials.html')

@app.route('/allusers')
def show_all_users():
	users = db_session.query(User).all()
	return jsonify(Users=[user.serialize for user in users])

@app.route('/photo/<path:filename>')
def uploaded_photo(filename):
	try:
		photo = db_session.query(Photo)\
			.filter_by(filename=filename).one()
	except:
		return 'There was an error with the photo.'
	
	return Response(io.BytesIO(photo.image_blob), mimetype='image/JPEG')
	# return send_file(
	# 	io.BytesIO(photo.image_blob),
	# 	attachment_filename=photo.filename,
	# 	mimetype='image/jpeg')

@app.route('/<file>')
def get_file(file):
	return render_template(file)

