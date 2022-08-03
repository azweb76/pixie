from tempfile import gettempdir, tempdir
from unittest.mock import patch
from pixie import engine
import tests
from pixie.runtime import PixieRuntime
from pixie.context import PixieContext


def test_main():
    class TestRuntime(PixieRuntime):
        logs = []
        def ask(self, prompt):
            return 'john'
        def log(self, message: str):
            self.logs.append(message)

    tmpdir = gettempdir()
    runtime = TestRuntime()
    context = PixieContext({
        '__target': tmpdir
    })

    package = tests.get_fixture('config')
    with patch('sys.stdout.write') as mock_write:
        engine.run(context, {
            'package': package
        }, runtime)
    # assert context == {
    #     'fname': 'john',
    #     'fullname': 'john doe',
    #     'lname': 'doe',
    #     'helloworldPackage': helloworldPackage,
    #     '__package': {
    #         'path': package,
    #         'options': {
    #             'package': package
    #         }
    #     },
    #     '__target': tmpdir
    # }
    assert context.notes == [
        ''''# test
fname: John
lname: Clayton
age: 20 # test comment
'''
    ]
    # assert context.todos == [
    #     'test todo from basic'
    # ]
