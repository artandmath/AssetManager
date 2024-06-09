"""Schema and tokens."""

# Import third party modules
# pylint: disable=import-error
import os
import re
import logging

# Import internal modules
from AssetManager import constants

def splitStringComponents(inputString):
    # This regex will match parts inside the curly braces and parts outside them
    # Iterate over the matches and add them to the components list
    # Each match is a tuple, one of the elements will be an empty string
    # depending on whether it matched the part inside or outside the braces

    pattern = r'\{(.*?)\}|([^{]+)'
    matches = re.findall(pattern, inputString)
    components = []
    for match in matches:
        components.append(match[0] if match[0] else match[1])
    return components

def schematokensListFromString(schemaStr):
    splitPath = schemaStr.split('/')[1:]

    tokensList = []
    for pathItem in splitPath:
        pathItemComponents = splitStringComponents(pathItem)

        tokens = []
        for component in pathItemComponents:
            token = {'key': component, 'type': constants.TOKEN_CONST, 'delimeter': '', 'isOptional': False}

            if component[0] == '*':
                token['isOptional'] = True
                component = component[1:]
                if len(component) == 0:
                    raise Exception("Contains a optional token with length of zero")

            if '@' in component or '#' in component:
                if component.count('@') > 1:
                    raise Exception("A token contains more than one @ char")
                if component.count('#') > 1:
                    raise Exception("A token contains more than one # char")
                if component.count('@') >= 1 and component.count('#') >= 1:
                    raise Exception("A token contains both # and @ chars")
                if component.find('@') > 1:
                    raise Exception("Delimeter before @ can only be one character")
                if component.find('#') > 1:
                    raise Exception("Delimeter before # can only be one character")

                if component[1] == '@' or component[1] == '#':
                    token['delimeter'] = component[0]
                    if token['delimeter'] not in constants.VALID_DELIMETERS:
                        raise Exception("Invalid delimeter")
                    component = component[1:]

                if component[0] == '@':
                    token['type'] = constants.TOKEN_EDIT_VAR
                if component[0] == '#':
                    token['type'] = constants.TOKEN_HIDDEN_VAR
                component = component[1:]
                token['key'] = component

            tokens.append(token)
        tokensList.append(tokens)
    return tokensList


def tokenizePathComponent (tokens, pathComponent):
    tokenizedComponents = []

    containsOptionalToken = False
    optionalIndex = None
    paddingOptional = False

    baseDelimeters = []
    extensionDelimeters = []

    i = 0
    for token in tokens:
        if token['isOptional'] == True and token['delimeter'] != '.':
            containsOptionalToken = True
            optionalIndex = i
        i+=1

    for token in tokens:
        if token['isOptional'] == True and token['delimeter'] == '.':
            paddingOptional = True

    base = pathComponent
    extension = ''
    if '.' in pathComponent:
        if pathComponent.count('.') > 2:
            raise Exception("There should not be more than two '.' characters in filename")
        if pathComponent.count('.') == 2 and paddingOptional != True:
            raise Exception("Padding is not optional in this pipeline. There should not be more than one '.' characters in filename")
        extension = pathComponent.split('.', 1)[1]
        base = pathComponent.split('.', 1)[0]
        
    # Fetch the delimeters
    for token in tokens:
        if token['type'] == constants.TOKEN_CONST:
            baseDelimeters.append(token['type'])
        else:
            if token['delimeter'] != '.':
                baseDelimeters.append(token['delimeter'])
            if token['delimeter'] == '.':
                extensionDelimeters.append(token['delimeter'])

    # Fetch the number of the tokens in the base part, split by delimeters (or constant tokens)
    # We need to know the count, in case we have variants in the token list
    i = 1
    base2 = base
    for token in tokens:
        if token['type'] == constants.TOKEN_CONST:
            base2 = base2.replace(token['key'], '')
            i+=1
        else:
            try:
                base2 = base2.split(token['delimeter'],1)[1]
                i+=1
            except:
                pass

    # Fetch the values for token keys for the base part of the path compontent
    for j in range(0,len(baseDelimeters),1):
        component = {'key':tokens[j]['key'], 'value':''}
        if tokens[j]['type'] == constants.TOKEN_CONST:
            base = base.replace(tokens[j]['key'], '', 1)
            tokenizedComponents.append(component)
        else:
            if j != optionalIndex:
                try:
                    value = base.split(tokens[j+1]['delimeter'],1)[0]
                    base = base.split(tokens[j+1]['delimeter'],1)[1]
                except:
                    value = base
                component['value'] = value
            else:
                if i == len(baseDelimeters):
                    try:
                        value = base.split(tokens[j+1]['delimeter'],1)[0]
                        base = base.split(tokens[j+1]['delimeter'],1)[1]
                    except:
                        value = base
                    component['value'] = value
                    tokenizedComponents.append(component)
                else:
                    component['value'] = None
            tokenizedComponents.append(component)

    # Fetch the values for token keys for the extension part of the path compontent
    if len(extensionDelimeters) == 0:
        return tokenizedComponents

    # Fetch the number of the tokens in the base part, split by delimeters (or constant tokens)
    # We need to know the count, in case we have variants in the token list
    padding = None
    if '.' in extension:
        padding = extension.split('.')[0]
        extension = extension.split('.')[1]

    component = {'key':tokens[-2]['key'], 'value':padding}
    tokenizedComponents.append(component)
    component = {'key':tokens[-1]['key'], 'value':extension}
    tokenizedComponents.append(component)
    return tokenizedComponents


class Schema():
    def __init__(self, schemaStr=''):
        super(Schema, self).__init__()

        if schemaStr == '':
            schemaStr = str(os.environ.get('ASSET_MANAGER_SCHEMA', constants.SCHEMA_DEFAULT))
        self.tokensList = schematokensListFromString(schemaStr)

    def updateSchemaFromString(self, schemaStr):
        self.tokensList = schematokensListFromString(schemaStr)

    @property
    def keys(self):
        keys = []
        for tokens in self.tokensList:
            for token in tokens:
                if token['type'] != constants.TOKEN_CONST:
                    if token['key'] not in keys:
                        keys.append(token['key'])
        return keys

    @property
    def keysEditable(self):
        keys = []
        for tokens in self.tokensList:
            for token in tokens:
                if token['key'] != token['delimeter']:
                    if token['key'] not in keys:
                        if token['type'] == constants.TOKEN_EDIT_VAR:
                            keys.append(token['key'])
        return keys

    @property
    def keysHidden(self):
        keys = []
        for tokens in self.tokensList:
            for token in tokens:
                if token['key'] != token['delimeter']:
                    if token['key'] not in keys:
                        if token['type'] == constants.TOKEN_HIDDEN_VAR:
                            keys.append(token['key'])
        return keys

    @property
    def keysOptional(self):
        keys = []
        for tokens in self.tokensList:
            for token in tokens:
                if token['optional']:
                    keys.append(token['key'])
        return keys

    @property
    def schemaPathHead(self):
        if len(self.tokensList) > 0:
            items = self.schemaPathItemsAsStringList()
            if self.isValid:
                return '/'+'/'.join(items[:-1])+'/'
        return ''
        #return 'invalid schema'

    @property
    def schemaPathTail(self):
        if len(self.tokensList) > 0:
            items = self.schemaPathItemsAsStringList()
            if self.isValid:
                return items[-1]
        return ''
        #return 'invalid schema'

    @property
    def schemaPathHeadColor(self):
        if len(self.tokensList) > 0:
            items = self.schemaPathItemsAsStringList(asHtmlWithColor=True)
            if self.isValid:
                return '/'+'/'.join(items[:-1])+'/'
        return ''
        #return '<font color="Red"><b>invalid schema</b></font>'

    @property
    def schemaPathTailColor(self):
        if len(self.tokensList) > 0:
            items = self.schemaPathItemsAsStringList(asHtmlWithColor=True)
            if self.isValid:
                return items[-1]
        return ''            
        #return '<font color="Red"><b>invalid schema</b></font>'
    
    @property
    def tokenColors(self):
        tokenColors = {}
        availableColors = constants.TOKEN_COLORS_LIST.copy()
        for tokens in self.tokensList:
            for token in tokens:
                if token['type'] == constants.TOKEN_EDIT_VAR:
                    if token['key'] not in tokenColors.keys():
                        tokenColors[token['key']] = availableColors.pop(0)
        return tokenColors
    
    @property
    def isValid(self):
        #basic validation, need to do this better
        if len(self.tokensList) > 1:
            return True
        return False

    def schemaPathItemsAsStringList(self, asHtmlWithColor=False):
        pathItems = []
        colorPathItems = []
        # Up to 18 token colors you crazy son of a gun (18 is a stupid amount of tokens)
        availableColors = constants.TOKEN_COLORS_LIST
        for tokens in self.tokensList:
            pathItem = ''
            colorPathItem = ''
            for token in tokens:
                tokenStr = ''
                colorTokenStr = ''
                if token['type'] == constants.TOKEN_CONST:
                    # for constants the token and delimeter are one and same
                    tokenStr = token['key']
                    colorTokenStr = tokenStr
                elif token['type'] == constants.TOKEN_HIDDEN_VAR:
                    tokenStr = token['delimeter'] + '#' + token['key']
                    colorTokenStr = '<font color="{0}"><b>{1}</b></font>'.format('SlateGray',tokenStr)
                else:
                    if token['type'] == constants.TOKEN_EDIT_VAR:
                        tokenStr = '@' + token['key']
                        colorTokenStr = tokenStr
                    colorName = self.tokenColors[token['key']]
                    enableColor = bool(os.environ.get('ASSET_MANAGER_ENABLE_COLOR', True))
                    if not enableColor: colorName = 'Silver'
                    colorTokenStr = '<font color="{0}"><b>{1}</b></font>'.format(colorName,tokenStr)

                    tokenStr = token['delimeter'] + tokenStr
                    colorTokenStr = token['delimeter'] + colorTokenStr

                if token['isOptional']:
                    tokenStr = '[' + tokenStr + ']'
                    colorTokenStr = '[' + colorTokenStr + ']'

                pathItem += tokenStr
                colorPathItem += colorTokenStr

            colorPathItems.append(colorPathItem)
            pathItems.append(pathItem)
        if asHtmlWithColor:
            return colorPathItems
        else:
            return pathItems


    def filePathToEditableTokens(self, filePathStr):
        splitPath = filePathStr.split('/')[1:]
        tokenDict = {}

        if len (splitPath) != len (self.tokensList):
            logging.info("The number of components in the file path should match the number of components in the schema when file path is split by '/'")
            for key in self.keysEditable:
                tokenDict[key] = constants.TOKEN_ERROR
            return tokenDict

        i = 0
        for pathItem in splitPath:
            tokens = tokenizePathComponent (self.tokensList[i], pathItem)
            for token in tokens:
                key = token['key']
                value = token['value']
                if key in self.keysEditable:
                    for key2 in tokenDict.keys():
                        if key == key2 and value != tokenDict[key2]:
                            logging.info('Mis-matched tokens in the filename. Setting key: {0} to value: {1}'.format(key, constants.TOKEN_ERROR))
                            value = constants.TOKEN_ERROR
                    tokenDict[key] = value
            i+=1
        return tokenDict

    def filePathToTokens(self, filePathStr):
        splitPath = filePathStr.split('/')[1:]
        tokenDict = {}

        if len (splitPath) != len (self.tokensList):
            logging.info("The number of components in the file path should match the number of components in the schema when file path is split by '/'")
            for key in self.keysEditable:
                tokenDict[key] = constants.TOKEN_ERROR
            return tokenDict

        i = 0
        for pathItem in splitPath:
            tokens = tokenizePathComponent (self.tokensList[i], pathItem)
            for token in tokens:
                key = token['key']
                value = token['value']
                tokenDict[key] = value
            i+=1
        return tokenDict

    def tokensToFilePath(self, userTokens):
        path = ''
        for tokens in self.tokensList:
            path = path + '/'
            for token in tokens:
                if token['type'] == constants.TOKEN_CONST:
                    path = path + token['key']
                else:
                    for key in userTokens.keys():
                        if userTokens[key] and key == token['key']:
                            path = path + token['delimeter'] + userTokens[key]
            
        return path
        