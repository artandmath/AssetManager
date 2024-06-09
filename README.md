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

Open the example nukescript for further documentation.

To disable color on the tokens and to disable the override field above the tokens, add the following environment variables with empty stirngs:

```bash
#! /bin/bash
#add these lines to your environment
ASSET_MANAGER_ENABLE_OVERRIDE=""
ASSET_MANAGER_ENABLE_COLOR=""
```

## Project Goals/Principals
- A schema syntax that can describe **most** VFX file systems schemas using a single string of text.
- A library that can use that schema for file IO in any DCC.
- Interoperable with OpenAsset IO.
- Work with filesystem if the database has failed, or as a stepping stone to developing a database. Without any filesytem breadcrumbs.
- Solve/Desolve system.
- Asset Importer.
- Asset Manager.
- Keep it simple. Simple enough for a non-VFX systems admin or technical artist to set up and manage.
- If the project needs to capture edge cases, consider whether that's the right way to do it.
- Always remain pipeline independant.
- Filesystem level only. The contents of files is outside the scope of the project.

## Investigations

- Shims between Asset Manager & SG Tank/Toolkit, Pyblish etc.

## Todo - long term
- Project roadmap
- Ground up re-write: using the Nuke panel Asset Manager prototype as a guide.
- Hooks for non-core functionality. eg - color code versions, group via file/token etc, version to latest, version to current, non-token spreadhseet columns etc.

## Known issues with prototype
- Any cell can be updated when we really only want to update items within one column.
- For example, click a row, modify a cell, evey token is written and you've killed your asset.
- Undo is performed with a sledgehammer. It's Apple Shake level stable.
- Pieces of code from node_table are still littered in the prototype. The comments within the code will likely be incorrect.
- Probably won't work with Microsoft Windows.
- Won't work with url paths "smb://" etc 

## Special thanks
- Thank you to Mitja Müller-Jend for his node_table panel for Nuke, which is used as the inspiration for this codebase. Your code is some of the most readable I've ever encountered: https://gitlab.com/filmkorn/nuke_node_table
