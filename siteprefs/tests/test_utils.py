from siteprefs.utils import Mimic


def test_mimic():

    class M(Mimic):

        def __init__(self, value):
            self._val = value

        @property
        def value(self):
            return self._val

    bool(M(False))

    assert M(4)() == 4
    assert str(M('www')) == 'www'
    assert bool(M('some'))
    assert len(M('some')) == 4
    assert int(M(4)) == 4
    assert float(M(4.2)) == 4.2
    assert not bool(M(False))
    assert not M(False)
    assert M(True)
    assert (M(4) + 5) == 9
    assert (5 + M(4)) == 9
    assert (M(4) - 5) == -1
    assert (5 - M(4)) == 1
    assert (M(4) * 5) == 20
    assert (5 * M(4)) == 20

    x = 5
    x += M(4)
    assert x == 9

    x = M(4)
    x -= 1
    assert x == 3

    assert ('some%s' % M('any')) == 'someany'
    assert (M('any') + 'some') == 'anysome'
    assert M(4) < 5
    assert M(4) <= 5
    assert M(6) > 5
    assert M(6) >= 5
    assert M(5) == 5
    assert M(4) != 5
    assert len(M('some')) == 4
    assert 'ome' in M('some')
