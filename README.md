# Item Catalog
Made with Python's Flask Framework
### Instructions for setting this file up

*Recommend using [virtualenv](https://virtualenv.pypa.io)*

1. Clone or download source
```
git clone https://github.com/nanomosfet/item-catalog.git
```
2. Install app from root of directory. That is, where setup.py is located.
```
pip install --editable .
```
3. Instruct flask to use the correct app
```
export FLASK_APP=item_catalog
```
4. Now you can run the server
```
flask run
```
5. Is it tested? You bet it is.
```
python item_catalog/tests.py
```
