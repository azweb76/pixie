from pixie import rendering
from pixie.context import PixieContext

def test_render_options():
    opts = rendering.render_options({
        'fname': '{{ context.fname }}',
        'list': [
            '{{ context.fname }}'
        ],
        'list_of_dicts': [
            { 'fname': '{{ context.fname }}' }
        ]
    }, PixieContext({
        'fname': 'john',
    }))

    assert opts == {
        'fname': 'john',
        'list': [
            'john'
        ],
        'list_of_dicts': [
            { 'fname': 'john' }
        ]
    }

def test_render_token():
    assert rendering.render_tokens('test: FNAME', PixieContext({
        'FNAME': 'john'
    })) == 'test: john'