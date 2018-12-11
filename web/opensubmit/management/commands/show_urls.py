# from https://gist.githubusercontent.com/andreif/263a3fa6e7c425297ffee09c25f66b20/raw/1c313b4d84505951f4d0e89587fd9ac543516444/show_urls.py

import sys
from django.core.management import BaseCommand
from django.conf.urls import RegexURLPattern, RegexURLResolver
from django.core import urlresolvers


def collect_urls(urls=None, namespace=None, prefix=None):
    if urls is None:
        urls = urlresolvers.get_resolver()
    prefix = prefix or []
    if isinstance(urls, RegexURLResolver):
        res = []
        for x in urls.url_patterns:
            res += collect_urls(x, namespace=urls.namespace or namespace,
                                prefix=prefix + [urls.regex.pattern])
        return res
    elif isinstance(urls, RegexURLPattern):
        # TODO: use here an OrderedDict for Python < 3.6
        return [{'namespace': namespace,
                 'name': urls.name,
                 'pattern': prefix + [urls.regex.pattern],
                 'lookup_str': urls.lookup_str,
                 'default_args': dict(urls.default_args)}]
    else:
        raise NotImplementedError(repr(urls))


def show_urls():
    all_urls = collect_urls()

    max_lengths = {}
    for u in all_urls:
        for k in ['pattern', 'default_args']:
            u[k] = str(u[k])
        for k, v in list(u.items())[:-1]:
            u[k] = v = v or ''
            # Skip app_list due to length (contains all app names)
            if (u['namespace'], u['name'], k) == \
                    ('admin', 'app_list', 'pattern'):
                continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))

    for u in sorted(all_urls, key=lambda x: (x['namespace'], x['name'])):
        sys.stdout.write(' | '.join(
            ('{:%d}' % max_lengths.get(k, len(v))).format(v)
            for k, v in u.items()) + '\n')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        show_urls()
