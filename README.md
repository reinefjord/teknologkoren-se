# teknologkoren-se

## Installation
Clone the repo, then run
```
python3 -m pip install -r requirements.txt
```
to install the dependencies.

## Create database
Use `manage.py` to create the database. `python3 manage.py full_setup` will
create the database, some useful tags and a user with the Webmaster tag.

## Running
### Flask development server
Set environment variable `FLASK_APP` to `teknologkoren_se/__init__.py`, then run
`flask run`. To enable debugging, set `FLASK_DEBUG` to `1`.

E.g.,
```
FLASK_APP=teknologkoren_se/__init__.py FLASK_DEBUG=1 flask run
```

Image paths have the optional /img(400|800|1600)/ which nginx understands but
Flask does not. Images with the resize path argument will return 404. For now,
use gunicorn and nginx instead.

### gunicorn/nginx
Install the nginx configs, changing `server_name` in `teknologkoren-se.conf`
to anything you like, for example `local.dev`. Add whatever you chose to your
hosts-file (`/etc/hosts`):
```
127.0.0.1 local.dev localhost
127.0.0.1 intranet.local.dev localhost
```
and add it as server name in config.py. `localhost` does not support subdomains
and will not work.

Run nginx (`systemctl start nginx`) and `run.sh` (`FLASK_DEBUG=1 ./run.sh`).
