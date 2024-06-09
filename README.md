# AssetManager
Asset Manager is a panel for Nuke that pulls the assets (ie.e nodes that have a 'file' knob) into rows in a spreadsheet. The spreadsheet allows the modification of values which are in turn written back to the 'file' knob of the node. The spreadsheet columns are determined by a one line schema string of tokens that describes the structure of the file system.
> [!CAUTION]
> Asset Manager is in a pre-release/protoype stage and is not intended for production use in its current state.

## Installation

Download Qt.py and add into your .nuke folder or PYTHON_PATH:
https://github.com/mottosso/Qt.py

Download the AssetManager folder and add into your .nuke folder or PYTHON_PATH.

Add to your menu.py:

```python
from nukescripts import panels

"""Asset Manager"""
def getAssetManagerWidget():
    from AssetManager import view as AssetManagerView
    return AssetManagerView.AssetManagerWidget()

panels.registerWidgetAsPanel(
    'getAssetManagerWidget',
    'Asset Manager',
    'com.danielharkness.AssetManager',
    False
)
```

To disable color on the tokens and to disable the override add the following environment variables with empty stirngs:

```bash
#! /bin/bash
#add these lines to your environment
ASSET_MANAGER_ENABLE_OVERRIDE=""
ASSET_MANAGER_ENABLE_COLOR=""
```


## Project Goals
- A schema syntax that can describe most VFX file-systems using a single string.
- A library that can use that schema for file IO in any DCC.
- Interoperable with OpenAsset IO.
- Work with filesystem if database has failed, or as a stepping stone to developing a database. And without breadcrumbs.
- Asset Importer.
- Asset Manager.
- Solve/Desolve system.
- Keep it simple. Simple enough for a non-VFX systems admin or technical artist to set up and manage.
- If the project needs to capture edge cases, consider whether that's the right way to do it.

## Investigations

- Shims between Asset Manager & SG Tank/Toolkit, Pyblish etc.

## Todo - long term
- Project roadmap
- Re-build from ground up— using the nuke Asset Manager prototype as a guide.
- Hooks for non-core functionality. eg - color code versions, group assets, version to latest, version to current etc.

## Known issues with prototype
- any cell will be updated

## Special thanks
- Thank you to Mitja for his node_table panel for nuke, which is use as the inspiration for this codebase: https://gitlab.com/filmkorn/nuke_node_table
