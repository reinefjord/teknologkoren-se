from flask import Blueprint, render_template
from app.models import User, Tag, UserTag


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
    users = User.select()
    board = {}
    tags = ['Ordförande', 'Vice ordförande', 'Kassör', 'Sekreterare',
            'PRoletär', 'Notfisqual', 'Qlubbmästare']

    tags_copy = list(tags)

    for tag in tags_copy:
        try:
            board[tag] = (users
                          .join(UserTag)
                          .join(Tag)
                          .where(Tag.name == tag)
                          .get())

        except User.DoesNotExist:
            tags.remove(tag)

    return render_template('general/kontakt.html', board=board, tags=tags)
