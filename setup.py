from setuptools import setup, find_packages

setup(
    name='item_catalog',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'sqlalchemy',
        'google-api-python-client',
        'Pillow'
    ],
)
