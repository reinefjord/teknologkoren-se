from flask import Blueprint, render_template
from app.forms import BookingForm


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def om_oss():
    return render_template('general/om-oss.html')


@mod.route('/boka/', methods=['GET', 'POST'])
def boka():
    form = BookingForm()
    if form.validate_on_submit():
        pass
    return render_template('general/boka.html', form=form)


@mod.route('/sjung/')
def sjung():
    return render_template('general/sjung.html')


@mod.route('/kontakt/')
def kontakt():
    return render_template('general/kontakt.html')
