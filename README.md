# KD Analyzer


### Installation
```
pip3.7 install git+https://github.com/yobayob/kd-analyzer
```


### Usage


Create `.kd-config.json` file:
```
cd ~/projects/my-awesome-project
kd init
```


Run:
```
kd
```

Result:
```json
{
    "main": {
        "deps": {
            "typing": 0.22,
            "re": 0.25,
            "logging": 0.06,
            "collections": 0.04,
            "pathlib": 0.02,
            "json": 0.07,
            "dataclasses": 0.04,
            "argparse": 0.03,
            "os": 0.3,
            "deps": 0.03,
            "subprocess": 0.04,
            "esprima": 0.02,
            "ast": 0.03,
            "marshmallow_dataclass": 0.02,
            "math": 0.01,
            "__future__": 0.03,
            "asyncio": 0.01
        },
        "authors": {
            "ekonechnyi": 1.0
        },
        "languages": {
            "python": 1.0
        },
        "feautures": [
            {
                "ekonechnyi": "ekonechnyi",
                "features": 0.8
            },
            {
                "ekonechnyi": "ekonechnyi",
                "tests": 0.07
            },
            {
                "ekonechnyi": "ekonechnyi",
                "refactoring": 0.08
            },
            {
                "ekonechnyi": "ekonechnyi",
                "bugs": 0.05
            }
        ]
    }
}

```

### Config

[Example](.kd-config.json)

All files from `.gitignore` go ignore (regexp!). 
You can specify custom path
```
"\\.css", "^test.*js$", ...
```

If required, write aliases for authors
```
{
   "name": "ekonechnyi",
   "aliases": [
        "e.konechnyi", 
        "ekonechnyi"
   ]
},
```
Specify the various modules:
```
{
    "name": "main",
    "path": "analyzer"
}, {
    "name": "frontend",
    "path": "frontend/src"
}
```


