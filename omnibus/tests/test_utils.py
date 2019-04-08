import sys
import pytest
import os
import json

sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')

from omnibus.libs.util import *


class TestUtils():

    def test_convert(self):
        d_test = {"name": b'spanish_inquisition'}    
        res = convert(d_test)

        assert isinstance(res['name'],str)

        d_tup = list(d_test.items())
        res =convert(d_tup[0])

        assert isinstance(res[1],str)
        d_list = [b'1',b'2',b'3']
        res = convert(d_list)
        for i in res:
            assert isinstance(i,str)

        sets = {b'1',b'3',b'4'}
        res = convert(sets)
        for i in res:
            assert isinstance(i,str)

    def test_collect_files(self):
        dirname = os.path.dirname(__file__)
        folder = '../../tests'
        ignores = '../../tests/ignore/test_generator.yml'

        folder = get_path(dirname,folder)
        ignores = get_path(dirname,ignores)
        ignores = [ignores]

        all_files = get_all(folder,ignores=ignores)

        assert ignores[0] not in all_files

         