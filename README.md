# AssetManager
Asset Manager is a panel for Nuke that pulls assets (i.e. nodes that have a 'file' knob) into rows in a spreadsheet. The spreadsheet allows the modification of values which are in turn written back to the 'file' knob of the node. The spreadsheet columns are determined by a one line string of tokens that describes the structure of the filesystem.
> [!CAUTION]
> Asset Manager is at a pre-release/protoype stage and not intended for production use in its current state. USE IT AT YOUR OWN RISK!

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
Open the AssetManager panel in Nuke from Windows:Custom:Asset Manager.

Hover cursor over the first text field for syntax to build a schema that matches your filesystem.

Open the AssetManagerDemo.nk nukescript for syntax examples.

To disable color on the tokens and to disable the override field above the tokens, add the following environment variables with empty stirngs:
```bash
#! /bin/bash
#add these lines to your environment
ASSET_MANAGER_ENABLE_OVERRIDE=""
ASSET_MANAGER_ENABLE_COLOR=""
```

## Project Goals/Principals
- A schema syntax that can describe _MOST_ VFX filesystem schemas using a single line of text.
- A library that can use that schema for file IO in any DCC.
- Keep it simple. Simple enough for a technical artist or non-VFX admin to set up and manage, not so complicated that it requires a software developer or TD(s).
- Interoperable with OpenAsset IO (probably as two lines of text, one for filesystem resolve, one for database resolve).
- Work in filesystem only mode if the database has failed, or as a stepping stone to developing a database. And without any filesytem breadcrumbs.
- If the project needs to capture edge cases, consider whether that's the right way to do it.
- Always remain pipeline independant.
- Filesystem/Database level only. Any item on disk for which Nuke has a node that contains a 'file' knob. What is contained inside an asset/file is outside the scope of the project.
- Artist first: outside of install and creating a token schema, if the UI requires reading the manual, it's too complicated.
- A UI suite:
  - Asset Manager (Nuke)
  - Solve/Desolve system (Nuke)
  - Asset Importer (Nuke, possibly standalone)

## Investigations

- Shims between AssetManager & SG Tank/Toolkit, Pyblish etc

## Todo - long term
- Revisit schema/token syntax, allow for some more flexibility and syntax that enables restrictions per token.
- Project roadmap
- Ground up re-write: using the Nuke panel Asset Manager prototype as a guide.
- Hooks/extensible for non-core functionality. eg - color code spreadsheet trext (for versions), group via file/token, select DAG per grouping, contextual right-click options, version to latest, version to current, non-token spreadhseet columns, thumbnails, row highlighting for errored/missing files, toolbar for user button/dropdowns etc etc.

## Special thanks
- Thank you to Mitja Müller-Jend for his node_table panel for Nuke. Your code is some of the most readable I've ever encountered: https://gitlab.com/filmkorn/nuke_node_table
- I apologize for basterdizing your wonderful code to hack together this prototype.

## Known issues with prototype
- Any cell can be updated when we really only want to update items within one column.
- For example, click a row, modify a cell, evey token is written and you've killed your asset.
- Undo is performed with a sledgehammer. It's Apple Shake-level stable.
- Pieces of code from node_table are littered throughout the prototype. The comments in the code are from node_table, as such will be 90% incorrect.
- Probably won't work with Microsoft Windows.
- Won't work with url paths "smb://" etc 
