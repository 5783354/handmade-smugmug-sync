import random
import string


def random_string(size=20):
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _x in range(size)
    ).capitalize()


def chunks(lst, size):
    for i in xrange(0, len(lst), size):
        yield lst[i:i + size]


def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join(
            '{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))
