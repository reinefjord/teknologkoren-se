#!/bin/bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel compile -d teknologkoren_se/translations
pybabel update -i messages.pot -d teknologkoren_se/translations
