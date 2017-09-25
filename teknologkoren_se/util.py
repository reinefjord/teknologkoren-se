from urllib.parse import urlparse, urljoin
from flask import url_for, request
from teknologkoren_se import app


def paginate(content, page, page_size):
    """Return a page of content.

    Calculates which posts to have on a specific page based on which
    page they're on and how many objects there are per page.
    """
    start_index = (page-1) * page_size
    end_index = start_index + page_size
    pagination = content[start_index:end_index]
    return pagination


def url_for_other_page(page):
    """Return url for a page number."""
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def is_safe_url(target):
    """Tests if the url is a safe target for redirection.

    Does so by checking that the url is still using http or https and
    and that the url is still our site.
    """
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        test_url.netloc in app.config['ALLOWED_HOSTS']


def get_redirect_target():
    """Get where we want to redirect to.

    Checks the 'next' argument in the request and if nothing there, use
    the http referrer. Also checks whether the target is safe to
    redirect to (no 'open redirects').
    """
    for target in (request.values.get('next'), request.referrer):
        if not target:
            continue
        if target == request.url:
            continue
        if is_safe_url(target):
            return target
