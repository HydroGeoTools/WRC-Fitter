# WRC-Fitter webapp

This is a simple web application that fit a Water Retention Curve using the specified model (Van Genuchten only for instance)

## Description

- `fitter.py` contains all the necessary backend functions, such as the optimization routines or the WRC models
- `main.py` contains the web application
- `wsgi.py` is the web server entry script


## Run local

```
git clone https://github.com/MoiseRousseau/WRC-Fitter
cd WRC-Fitter
pip install -r requirements.txt
python main.py
```


## How to deploy

Deployment is done within a Docker container and throught the Dokku PaaS tool.
See [Dokku installation docs](https://dokku.com/docs/getting-started/installation/).

In addition, modify the ssh config file to use the configure the Dokku git server, such as:
```
Host dokku_server
    HostName localhost
    User dokku
    IdentityFile ~/.ssh/id_ed25519_dokku
```

1. Download App and configure Dokku repo:
```
git clone https://github.com/MoiseRousseau/WRC-Fitter
cd WRC-Fitter
git remote add dokku dokku_server:wrc-fitter
```

2. Create Dokku apps and deploy:
```
dokku apps:create wrc-fitter
git push dokku master:master --verbose
```


## TODO

* Let user adjust manually the final result
* Allow other WRC models
* Check the point density, i.e. an isolated point is as important as many clustered points
