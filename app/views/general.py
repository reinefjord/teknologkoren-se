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
    # FIXME!
    class contact:
        """!!!PLACEHOLDER!!!"""
        def __init__(self, role, name, email):
            self.role = role
            self.name = name
            self.email = email

    contacts = [
            contact("Ordförande", "Namn Efternamn", "ordf@teknologkoren.se"),
            contact("Vice ordförande", "Namn Efternamn", "vice@teknologkoren.se"),
            contact("Kassör", "Namn Efternamn", "pengar@teknologkoren.se")
    ]

    return render_template('general/kontakt.html', contacts=contacts)
