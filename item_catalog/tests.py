import os
import unittest
import item_catalog
from StringIO import StringIO
from database_setup import User




class item_catalog_tests(unittest.TestCase):
    def login(self):
        """Crude way to test Login Due with fake credentials.
        """
        with self.app as c:
            with c.session_transaction() as session:
                user = User(gid=1234, name='Timothy Searcy')
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
            description='Yellow Curved',
            category='Fruit'), follow_redirects=True)
        assert b'Banana' in post_result.data
        assert b'Fruit' in post_result.data
        assert b'All Items:' in post_result.data
        result = self.app.get('/item/1/edit', follow_redirects = True)
        assert b'Banana' in result.data
        assert b'Fruit' in result.data
        assert b'Edit Item' in result.data
        post_result = self.app.post('/item/1/edit', data=dict(
            name='Apple',
            description='Red',
            category='Fruit'), follow_redirects=True)
        assert b'Apple' in post_result.data
        assert b'Banana' not in post_result.data
        post_result = self.app.post('/item/1/delete', follow_redirects=True)
        assert b'Apple' not in post_result.data
        assert b'Banana' not in post_result.data
        assert b'Fruit' not in post_result.data

    def test_photo_add_delete(self):
        # TODO: Write tests for photo add and delete
        self.login()
        result = self.app.get('/add', follow_redirects=True)
        assert b'Signed in as Timothy Searcy' in result.data
        assert b'<h1>Add Item</h1>' in result.data
        post_result = self.app.post('/add', data=dict(
            name='Banana',
            description='Yellow Curved',
            category='Fruit'), follow_redirects=True)
        assert b'Banana' in post_result.data
        assert b'Fruit' in post_result.data
        assert b'All Items:' in post_result.data
        with open('item_catalog/test_files/1.jpg', 'rb') as test_photo:
            imgStringIO = StringIO(test_photo.read())
            print test_photo.read()
        post_photo = self.app.post(
            '/item/1/upload_photo',
            content_type='multipart/form-data',
            data=dict(
                {'file': (imgStringIO, '1.jpg')}),
            follow_redirects=True)
        assert b'<img' in post_photo.data
        delete_photo = self.app.post('/item/1/delete_photo/1', follow_redirects=True)
        assert b'<img' not in delete_photo.data



    def test_add_item_no_login(self):
        result = self.app.get('/add', follow_redirects=True)
        assert b'<h1>Credentials Page</h1>' in result.data








    def test_show_items_by_category(self):
        result = self.app.get('/category/JSON')
        self.assertEqual(result.status_code, 200)





if __name__ == '__main__':
    unittest.main()