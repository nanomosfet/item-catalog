# Item Catalog
Made with Python's Flask Framework
### Instructions for setting this file up

*Recommend using [virtualenv](https://virtualenv.pypa.io)*

1. Clone or download source
```
$ git clone https://github.com/nanomosfet/item-catalog.git
```
2. Install app from root of directory. That is, where setup.py is located.
```
$ pip install --editable .
```
3. Instruct flask to use the correct app
```
$ export FLASK_APP=item_catalog
```
4. Set up your Database
Export your SQLAlchemy database URI and Cloud Storage Bucket environment variables:
```
$ export SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://[USER]:[PASSWORD]@/[DATABASE]?host=/cloudsql/[INSTANCE NAME]
$ export CLOUD_STORAGE_BUCKET=[BUCKET NAME]
```
Note if you will be deploying this to a Google App Engine server make sure to edit the app.yaml file and include the environement variables in the file.

Run the local connection to Cloud SQL using `cloud_sql_proxy.exe`
```
# Example on windows powershell:
$ .\cloud_sql_proxy.exe -instances=[INSTANCE NAME]=tcp:5432 -credential_file=[PATH TO YOUR CREDENTIALS FILE]
```

For more info on using Cloud SQL and Cloud Storage please visit [Using Cloud Storage](https://cloud.google.com/appengine/docs/flexible/python/using-cloud-storage) [Using Cloud SQL - PostgreSQL](https://cloud.google.com/appengine/docs/flexible/python/using-cloud-sql-postgres)

5. Now you can run the server
```
flask run
```
6. Is it tested? You bet it is.
```
python item_catalog/tests.py
```
