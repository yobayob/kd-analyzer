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
    "name": "kd-analyzer",
    "repository": "https://github.com/yobayob/kd-analyzer.git",
    "modules": [
        {
            "name": "main",
            "dependencies": [
                {
                    "name": "re",
                    "percent": 0.14
                },
                {
                    "name": "typing",
                    "percent": 0.19
                },
                {
                    "name": "dataclasses",
                    "percent": 0.06
                },
                {
                    "name": "os",
                    "percent": 0.1
                },
                {
                    "name": "json",
                    "percent": 0.1
                },
                {
                    "name": "marshmallow_dataclass",
                    "percent": 0.02
                },
                {
                    "name": "math",
                    "percent": 0.02
                },
                {
                    "name": "collections",
                    "percent": 0.07
                },
                {
                    "name": "__future__",
                    "percent": 0.04
                },
                {
                    "name": "ast",
                    "percent": 0.01
                },
                {
                    "name": "esprima",
                    "percent": 0.01
                },
                {
                    "name": "subprocess",
                    "percent": 0.03
                },
                {
                    "name": "logging",
                    "percent": 0.05
                },
                {
                    "name": "asyncio",
                    "percent": 0.03
                },
                {
                    "name": "gitlog",
                    "percent": 0.05
                },
                {
                    "name": "argparse",
                    "percent": 0.05
                },
                {
                    "name": "pathlib",
                    "percent": 0.02
                },
                {
                    "name": "sys",
                    "percent": 0.02
                }
            ],
            "authors": [
                {
                    "name": "ekonechnyi",
                    "percent": 1.0
                }
            ],
            "languages": [
                {
                    "name": "python",
                    "percent": 1.0
                }
            ],
            "features": [
                {
                    "name": "ekonechnyi",
                    "feature": "bugs",
                    "percent": 0.06
                },
                {
                    "name": "ekonechnyi",
                    "feature": "features",
                    "percent": 0.94
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


