# Item Catalog
### Instructions for setting this file up

*Recommend using [virtualenv](https://virtualenv.pypa.io)*

1. Install app from root of directory. That is, where setup.py is located.
```
pip install --editable .
```
2. Instruct flask to use the correct app
```
export FLASK_APP=item_catalog
```
3. Now you can run the server
```
flask run
```
