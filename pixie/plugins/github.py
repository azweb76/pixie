from pixie.steps import PixieStep
from github import Github

import os
from ruamel.yaml import YAML

from ..plugin import PixiePluginContext


def init(context: PixiePluginContext):
    context.add_step('github', GithubStep())


def fetch_token(options, context):
    if 'token' in options:
        return options['token']

    host = options.get('host', 'github.com')
    gh_hosts = os.path.expanduser('~/.config/gh/hosts.yml')
    if os.path.exists(gh_hosts):
        yaml = YAML()
        with open(gh_hosts, 'r') as f:
            gh_hosts = yaml.load(f)
        if host in gh_hosts:
            return gh_hosts[host]['oauth_token']
    
    return context.environ.get('GITHUB_TOKEN')


def get_base_url(host):
    if host == 'github.com':
        return f'https://api.{host}'
    return f'https://{host}/api/v3'


class GithubStep(PixieStep):
    def resolve_fn(self, obj_name, fn_name, context, step):
        options = step.get('with', {})
        host = options.get('host', 'github.com')
        base_url = get_base_url(host)
        token = fetch_token(options, context)
        g = Github(token, base_url=base_url)
        return getattr(g, fn_name), False
