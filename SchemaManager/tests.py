import logging
import sys
from schema import SchemaManager

def test(asset):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
    SCHEMA_DEFAULT = '//jobs.local/sharename/shows\
{/@show}{/@episode}{/@sequence}{/@shot}/{#product}{/@role}{/@task}{?/@user}\
{/@show}{_@episode}{_@sequence}{_@shot}{_@role}{_@task}{_@asset}{?_@variant}{_@version[v3]}{_@resolution}\
{/@show}{_@episode}{_@sequence}{_@shot}{_@role}{_@task}{_@asset}{?_@variant}{_@version[v3]}{_@resolution}{?.#padding}{.#extension}'

    schema_manager = SchemaManager(path_str=SCHEMA_DEFAULT)
    print(SCHEMA_DEFAULT, '\n\n')

    token_dict = {'show':'rrr',
                  'episode': 101,
                  'sequence': 'fb2',
                  'shot': 1234,
                  'product': 'renders',
                  'role': 'comp',
                  'task': 'precomp',
                  'asset': asset,
                  'version': 'v001',
                  'padding': '%04d',
                  'resolution': '1080p',
                  'extension': 'exr'}
    print(token_dict, '\n\n')

    path_from_dict = schema_manager.path_from_dict(token_dict=token_dict)
    print (path_from_dict, '\n\n')

    dict_from_path = schema_manager.dict_from_path(path_str=path_from_dict)
    print (dict_from_path, '\n\n')


test('testAsset_with_multidelimited_name')
#test('testAssetUndelimitedName')