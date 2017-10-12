# teknologkoren-se

## Installation with Pipenv
Make sure [Pipenv is installed](https://pipenv.readthedocs.io/en/latest/basics.html#installing-pipenv).
Clone and change directory to the repo, then run
```
pipenv install                      # Create virtualenv and install deps
pipenv shell                        # Spawn a shell with our environment
nodeenv -p -r npm-requirements.txt  # Install node.js requirements
```
You can exit out of the shell with `exit` or `^D`

## Create database
Use `manage.py` to setup everything. `python3 manage.py full_setup` will
create the database, which is pretty much all you need.

## Running
### Flask development server
Set environment variable `FLASK_APP` to `teknologkoren_se/__init__.py`, then run
`flask run`. To enable debugging, set `FLASK_DEBUG` to `1`.

E.g.,
```
FLASK_APP=teknologkoren_se/__init__.py FLASK_DEBUG=1 flask run
```

Image paths have the optional /img(400|800|1600)/ which nginx understands but
Flask's developement server does not. Images with the resize path argument will
return 404. Setting `DEBUG = True` in the config will however enable redirection
of those paths to the original image, making it possible to use Flask's server.
