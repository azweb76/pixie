import os

tests_dir = os.path.dirname(__file__)

def get_fixture(path):
    return os.path.join(tests_dir, 'fixtures', path)
