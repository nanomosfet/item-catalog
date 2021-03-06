import os
import unittest
import item_catalog
from StringIO import StringIO
from models import User, Photo, Item, Shopping_Cart_Item
from database import db_session, init_db
init_db()


class item_catalog_tests(unittest.TestCase):
    def login(self):
        """Crude way to test Login Due with fake credentials.
        """
        with self.app as c:
            with c.session_transaction() as session:
                user = User(gid=1234, name='Timothy Searcy')
                db_session.add(user)
                db_session.commit()
                user = db_session.query(User).filter_by(name='Timothy Searcy').one()
                session['user_name'] = user.name
                session['user_id'] = user.id
                session['user_gid'] = user.gid
                
        return self.app.get('/', follow_redirects=True)

    def logout(self):
        result = self.app.get('/gdisconnect', follow_redirects=True)
        return result


    def setUp(self):
        item_catalog.app.testing = True
        item_catalog.app.config['SECRET_KEY'] = 'sekrit!'
        with item_catalog.app.app_context():
            item_catalog.clear_DB()
        self.app = item_catalog.app.test_client()


    def tearDown(self):
        self.logout()
        pass

    def test_login_logout(self):
        result = self.login()
        assert b'Signed in as Timothy Searcy' in result.data
        result = self.logout()
        assert  b'Signed in as Timothy Searcy' not in result.data

    def test_show_all_items_empty(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)

    def test_add_edit_delete_item_with_login(self):
        self.login()
        result = self.app.get('/add', follow_redirects=True)
        assert b'Signed in as Timothy Searcy' in result.data
        assert b'<h1>Add Item</h1>' in result.data
        post_result = self.app.post('/add', data=dict(
            name='Banana',
            price='1.12',
            description='Yellow Curved',
            category='Fruit'), follow_redirects=True)
        assert b'Banana' in post_result.data
        assert b'Fruit' in post_result.data
        assert b'All Items:' in post_result.data
        banana = db_session.query(Item).filter_by(name='Banana').one()

        result = self.app.get('/item/%s/edit' % banana.id, follow_redirects = True)
        assert b'Banana' in result.data
        assert b'Fruit' in result.data
        assert b'Edit Item' in result.data
        post_result = self.app.post('/item/%s/edit' % banana.id, data=dict(
            name='Apple',
            price='2.32',
            description='Red',
            category='Fruit'), follow_redirects=True)
        assert b'Apple' in post_result.data
        assert b'Banana' not in post_result.data
        post_result = self.app.post('/item/%s/edit' % banana.id, follow_redirects=True)
        assert b'Apple' not in post_result.data
        assert b'Banana' not in post_result.data
        assert b'Fruit' not in post_result.data

    def test_photo_add_delete(self):
        # TODO: Write tests for photo add and delete
        self.login()
        result = self.app.get('/add', follow_redirects=True)
        assert b'<h1>Add Item</h1>' in result.data
        post_result = self.app.post('/add', data=dict(
            name='Banana',
            price='2.32',
            description='Yellow Curved',
            category='Fruit'), follow_redirects=True)
        assert b'Banana' in post_result.data
        assert b'Fruit' in post_result.data
        assert b'All Items:' in post_result.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        with open('item_catalog/test_files/1.jpg', 'rb') as test_photo:
            imgStringIO = StringIO(test_photo.read())
            print test_photo.read()
        post_photo = self.app.post(
            '/item/%s/upload_photo' % banana.id,
            content_type='multipart/form-data',
            data=dict(
                {'file': (imgStringIO, '1.jpg')}),
            follow_redirects=True)
        assert b'<img' in post_photo.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        delete_photo = self.app.post(
            '/item/%s/delete_photo/%s' % (banana.id, banana.photos[0].id),
            follow_redirects=True)
        assert b'<img' not in delete_photo.data

    def test_cart(self):
        self.login()
        post_result = self.app.post('/add', data=dict(
            name='Banana',
            price='2.32',
            description='Yellow Curved',
            category='Fruit'), follow_redirects=True)
        get_empty_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $0' in get_empty_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        add_to_cart = self.app.post('/item/%d/addtocart' % banana.id, follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $2.32' in get_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        add_to_cart = self.app.post('/item/%d/addtocart' % banana.id, follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $4.64' in get_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        cart_item = db_session.query(Shopping_Cart_Item).filter_by(item=banana).first()
        delete_from_cart = self.app.post(
            '/deletefromcart/%d' % cart_item.id,
            follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $2.32' in get_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        cart_item = db_session.query(Shopping_Cart_Item).filter_by(item=banana).first()
        delete_from_cart = self.app.post(
            '/deletefromcart/%d' % cart_item.id,
            follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $0' in get_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        add_to_cart = self.app.post('/item/%d/addtocart' % banana.id, follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $2.32' in get_cart.data
        banana = db_session.query(Item).filter_by(name='Banana').one()
        delete_item = self.app.post('/item/%d/delete' % banana.id, follow_redirects=True)
        get_cart = self.app.get('/showcart', follow_redirects=True)
        assert b'Total $0' in get_cart.data

    def test_add_item_no_login(self):
        result = self.app.get('/add', follow_redirects=True)
        assert b'<h1>Credentials Page</h1>' in result.data

    def test_show_items_by_category(self):
        result = self.app.get('/category/JSON')
        self.assertEqual(result.status_code, 200)

if __name__ == '__main__':
    unittest.main()