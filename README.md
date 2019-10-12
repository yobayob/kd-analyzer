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
    "name": "for-selectel",
    "repository": "https://github.com/yobayob/for-selectel.git",
    "modules": [
        {
            "name": "main",
            "dependencies": {
                "typing": 0.2,
                "re": 0.15,
                "marshmallow_dataclass": 0.02,
                "dataclasses": 0.05,
                "os": 0.1,
                "json": 0.1,
                "collections": 0.06,
                "math": 0.02,
                "__future__": 0.05,
                "ast": 0.01,
                "esprima": 0.01,
                "subprocess": 0.03,
                "argparse": 0.05,
                "asyncio": 0.03,
                "gitlog": 0.05,
                "logging": 0.05,
                "sys": 0.02,
                "pathlib": 0.02
            },
            "authors": {
                "ekonechnyi": 1.0
            },
            "languages": {
                "python": 1.0
            },
            "feautures": [
                {
                    "name": "ekonechnyi",
                    "features": 1.0
                }
            ]
        }
    ]
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


