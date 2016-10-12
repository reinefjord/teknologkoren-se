from flask import Blueprint, render_template


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def om_oss():
    return render_template('general/om-oss.html')


@mod.route('/boka/', methods=['GET', 'POST'])
def boka():
    return render_template('general/boka.html')


@mod.route('/sjung/')
def sjung():
    return render_template('general/sjung.html')


@mod.route('/kontakt/')
def kontakt():
    return render_template('general/kontakt.html')
