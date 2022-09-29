import boto3

from ruamel.yaml import YAML

from pixie.rendering import render_options

from ..steps import PixieStep
from ..plugin import PixiePluginContext


def init(context: PixiePluginContext):
    context.add_step('aws', AwsStep())


class AwsStep(PixieStep):
    def resolve_fn(self, obj_name, fn_name: str, context, step):
        fn_parts = fn_name.split(':')
        options = render_options(step.get('with', {}), context)
        credentials = options.get('credentials', {})
        client_name = fn_parts[0]
        fn_name = fn_parts[1]
        session = boto3.Session(**credentials)

        aws_client = session.client(client_name)
        return getattr(aws_client, fn_name), False
