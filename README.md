# WRC-Fitter webapp

This is a simple web application that fit a Water Retention Curve using the specified model (Van Genuchten only for instance)

## Description

- `fitter.py` contains all the necessary backend functions, such as the optimization routines or the WRC models
- `main.py` contains the web application
- `main.ini` contains the configuration of the uwsgi server
- `wsgi.py` is the web server entry script
- `web-WRC-Fitter.service` is the systemd service configuration file


## How to deploy

0. Install system dependencies (Python server, Git, ...):
```
apt update && apt upgrade
apt install python3-virtualenv nginx uwgsi uwsgi-plugin-python3 python3-uwsgi git
```

1. Create a Python virtual environment for the application and install dependencies listed in `requirements.txt`:
```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

2. Configure nginx to route incomming trafic to the WSGI server, something such as:
``` 
cp WRC-Fitter.nginx /etc/nginx/sites-available/WRC-Fitter
ln -s /etc/nginx/sites-available/WRC-Fitter /etc/nginx/sites-enabled/WRC-Fitter
systemd restart nginx
```

3. Start WSGI server with:
```
uwsgi main.ini --plugin python > app.log 2>&1 &
#stop it with: uwsgi --stop ./myapp.pid  
```
In case you have a Python library error, an possible fix would be to create a symlink for `plugin_python.so` as is doesn't exist in `usr/lib/uwsgi/plugins`:
```
sudo ln -s /usr/lib/uwsgi/plugins/python310_plugin.so /usr/lib/uwsgi/plugins/python_plugin.so
``` 

4. Configure the systemd service so the web application is automatically started on boot:
```
cp web-WRC-Fitter.service /etc/systemd/system
systemctl daemon-reload
systemctl enable web-WRC-Fitter
systemctl start web-WRC-Fitter
```

## TODO

- Use a Unix socket for proxying
- Let user adjust manually the final result
- Allow other WRC models
