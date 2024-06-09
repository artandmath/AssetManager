# AssetManager
Asset Manager is a panel for Nuke that pulls the assets (ie.e nodes that have a 'file' knob) into rows in a spreadsheet. The spreadsheet allows the modification of values which are in turn written back to the 'file' knob of the node. The spreadsheet columns are determined by a one line schema string of tokens that describes the structure of the file system.
> [!CAUTION]
> Asset Manager is in a pre-release/protoype stage and is not intended for production use in its current state.

## Project Goals
- A schema syntax that can describe most VFX file-systems using a single string.
- A library that can use that schema for file IO in any DCC.
- Interoperable with OpenAsset IO
- Asset Importer.
- Asset Manager.
- Solve/Desolve system.
- Keep it simple. If we're looking to capture edge cases, we probably need to think whether that's the right way to do it.

## Investigstions

- SG Tank/Toolkit, Pyblish.

## Todo
- Re-build from ground up— using the prototype project.
