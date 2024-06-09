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
