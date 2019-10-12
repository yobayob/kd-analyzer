from setuptools import setup, find_packages

attrs = {
    "name": "kd",
    "include_package_data": True,
    "version": '0.0.1',
    "packages": find_packages(),
    "license": "",
    "zip_sage": True,
    "install_requires": [
        "esprima==4.0.1",
        "marshmallow==3.2.1",
        "marshmallow-dataclass==6.0.0"
    ],
    "entry_points": {
        "console_scripts": [
            'kd = analyzer.main:main'
        ],
    }
}

setup(**attrs)