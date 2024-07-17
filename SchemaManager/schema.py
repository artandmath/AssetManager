"""Schema class parses Asset Wrangler's token syntax."""

# Import third party modules
import logging
import sys
import re
from pathlib import PureWindowsPath #Path, PurePosixPath, PosixPath,

# Import internal modules
import constants as K

class Token():
    def __init__(self, token_str='') -> None:
        self._key = None
        self._value = None
        self._delimeter = None
        self._is_optional = False
        self._is_constant = False
        self._is_hidden = False
        self._is_version = False
        self._version_syntax = None
        self._is_valid = False
        self._validate(token_str=token_str)
        self._is_valid = True

    def __str__(self) -> str:
        return (self._short_description)
    
    def __repr__(self) -> str:
        return (self._short_description)

    @property
    def _short_description(self):
        string = ''
        if self._delimeter:
            string += str(self._delimeter)
        if self._is_hidden and not self._is_constant:
            string += K.HIDDEN_CHAR
        if self.is_editable:
            string += K.EDITABLE_CHAR
        string += self.key
        if self._is_version:
            string += f"[{self._version_syntax}]"
        if self._is_optional:
            string += K.OPTIONAL_CHAR
        if self.value:
            string += f"; value='{self.value}'"
        return f"{string}"
    
    @property
    def _long_description(self):
        #return f"{super().__repr__()}; {self._short_description}"
        #return f"schema.Token object; {self._short_description}"
        return f"Token='{self._short_description}'"

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        if self._is_constant:
            return self.key
        return self._value

    @property
    def delimeter(self):
        return self._delimeter

    @property
    def is_constant(self):
        return self._is_constant

    @property
    def is_optional(self):
        return self._is_optional

    @property
    def is_hidden(self):
        return self._is_hidden or self._is_constant

    @property
    def is_editable(self):
        return not self._is_hidden and not self._is_constant
    
    @property
    def is_valid(self):
        return self._is_valid

    @property
    def is_version(self):
        return self._is_version

    @property
    def dict(self) -> dict:
        token_dict = {}
        token_dict['key'] = self._key
        token_dict['value'] = self._value
        token_dict['delimeter'] = self._delimeter
        token_dict['is_optional'] = self._is_optional
        token_dict['is_constant'] = self._is_constant
        token_dict['is_hidden'] = self._is_hidden
        token_dict['is_version'] = self._is_version
        token_dict['version_syntax'] = self._version_syntax
        return token_dict
    
    @property
    def path(self) -> str:
        return self.delimeter + self.value
    
    def path_from_str(self, value_str='') -> str:
        return self.delimeter + value_str

    def _validate(self, token_str='') -> bool:
        hide = K.HIDDEN_CHAR
        edit = K.EDITABLE_CHAR
        option = K.OPTIONAL_CHAR
        original_str = token_str

        matches = re.match(K.VERSION_MATCH_BRACES, token_str)
        if matches:
            token_str = matches.group(1)
            self._is_version = True
            self._version_syntax = matches.group(2)

        if option in token_str:
            if not K.ALLOW_MULTIDELIMITED_TOKEN or '.' in token_str:
                self._is_optional = True
                token_str = token_str.replace(option, '')
            else:
                error_string = f"K.ALLOW_MULTIDELIMITED_TOKEN is set to True.\
Failed to create a optional token from string: '{original_str}'" 
                logging.critical(error_string)
                raise LookupError (error_string)
        if token_str[0] in K.DELIMETERS:
            self._delimeter = token_str[0]
            token_str = token_str[1:]
        if edit not in token_str and hide not in token_str:
            self._is_constant = True
        if hide in token_str:
            self._is_hidden = True
            token_str = token_str.replace(hide, '')
        if edit in token_str:
            token_str = token_str.replace(edit, '')
        if token_str and re.match(K.TOKEN_KEY_MATCH, token_str):
            self._key = token_str
            #logging.debug('call _validate(%s)\nTOKEN: %s\n', self, self.dict)
            return True
        error_string = f"Failed to create a token from string: \'{original_str}\'"
        logging.critical(error_string)
        raise Exception (error_string)


class SchemaManager():
    def __init__(self, path_str='', url_str='') -> None:
        super(SchemaManager, self).__init__()
        self._path_str = path_str
        self._url_str = url_str
        self._tokens_list = []
        self._errors = []
        self._validate()

    @property
    def path(self) -> str:
        path = self._path_str
        path = path.replace('\\', K.DELIMETERS[0])
        for delimeter in K.DELIMETERS:
            path = path.replace('%s{' % (delimeter), '{%s' % (delimeter))
        #logging.debug('call path(%s)\nPATH: %s\n' ,self, path)
        return path

    @path.setter
    def path(self, value):
        self._path_str = value
        self._validate()

    @property
    def anchor(self) -> str:
        dels = K.DELIMETERS
        anchor = PureWindowsPath(self._path_str.replace('\\','/')).anchor
        anchor = anchor.replace('\\', dels[0])[:-1]
        #logging.debug('call anchor(%s)\nPATH ANCHOR: %s\n' ,self, anchor)
        return anchor

    @property
    def unanchored_path(self):
        path = self.path
        if path.startswith(self.anchor):
            path = path.replace(self.anchor, '', 1)
        #logging.debug('call unanchored_path(%s)\nUNANCHORED PATH: %s\n' ,self, path)
        return path

    @property
    def is_valid(self) -> bool:
        # Return true if no errors in error stack
        return not bool(len(self._errors))

    @property
    def errors(self) -> list:
        return self._errors

    @property
    def keys(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            key_list.append(token.key)
        return list(set(key_list))

    @property
    def keys_editable(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            if token.is_editable:
                key_list.append(token.key)
        return list(set(key_list))

    @property
    def keys_hidden(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            if token.is_hidden:
                key_list.append(token.key)
        return list(set(key_list))

    @property
    def keys_optional(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            if token.is_optional:
                key_list.append(token.key)
        return list(set(key_list))

    @property
    def keys_non_optional(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            if not token.is_optional:
                key_list.append(token.key)
        return list(set(key_list))

    @property
    def keys_non_editable(self) -> list:
        key_list = []
        for token in self.token_list_flattened:
            if not token.is_editable:
                key_list.append(token.key)
        return list(set(key_list))

    @property
    def optional_directory_token_index(self) -> int:
        index = 0
        for token_group in self.tokens_list:
            if token_group[0][0].is_optional:
                return index
            index += 1
        return None

    @property
    def optional_directory_token(self) -> Token:
        index = self.optional_directory_token_index
        if index:
            return self.tokens_list[index][0][0]
        return None

    @property
    def tokens_list(self) -> list:
        return self._tokens_list

    @property
    def token_list_flattened(self) -> list:
        return list(self._flatten_list(self._tokens_list))

    def _flatten_list(self, list_in):
        if isinstance(list_in, list):
            for l in list_in:
                for y in self._flatten_list(l):
                    yield y
        else:
            yield list_in

    def optional_token_index(self, tokens_list=None) -> int:
        if not tokens_list:
            tokens_list = []
        index = 0
        for token in tokens_list:
            if token.is_optional:
                return index
            index += 1
        return None

    def optional_token(self, tokens_list=None) -> Token:
        if not tokens_list:
            return None
        index = self.optional_token_index(tokens_list=tokens_list)
        if index:
            return tokens_list[index]
        return None

    def _lists_from_path(self, path_str='') -> list:
        if path_str.startswith(self.anchor):
            path_str = path_str.replace(self.anchor, '', 1)
        dels = K.DELIMETERS
        path_lists = []
        level1_list = []
        level2_list = []
        for left_str in path_str.split(dels[0]):
            if left_str:
                if dels[2] in left_str:
                    split = left_str.split(dels[2],1)
                    left_str = split[0]
                    right_str = split[1]
                    level2_list = right_str.split(dels[2])
                    level1_list.append(level2_list)
                    level2_list = []
                level2_list = left_str.split(dels[1])
                level1_list.insert(0, level2_list)
                path_lists.append(level1_list)
                level1_list = []
                level2_list = []
        return path_lists

    def dict_from_path(self, path_str='') -> dict:
        lists = self._lists_from_path(path_str=path_str)
        tokens_list = self.tokens_list
        available_keys = self.keys
        used_keys = []
        token_dict = {}

        if len(lists) != len(tokens_list):
            index = 0
            for tokens in tokens_list:
                first_token = tokens[0][0]
                if first_token.delimeter == K.DELIMETERS[0]\
                and first_token.is_optional:
                    del tokens_list[index]
                    break
                index += 1
        for list, tokens_list in zip(lists, self.tokens_list):
            for values, tokens in zip(list, tokens_list):
                if len(values) != len(tokens):
                    index = 0
                    if K.ALLOW_MULTIDELIMITED_TOKEN:
                        for token in tokens:
                            if token.is_version:
                                values_left = values[0:index-1]
                                values_right = values[-len(tokens)+index:]
                                values_middle = values[index-1:-len(tokens)+index]
                                concatenate_middle_values = K.DELIMETERS[1].join(values_middle)
                                values_left.append(concatenate_middle_values)
                                values = values_left+values_right
                            index += 1
                    else:
                        for token in tokens:
                            if token.is_optional:
                                del tokens[index]
                                break
                            index += 1
                for value, token in zip(values, tokens):
                    if token.key in available_keys:
                        token_dict[token.key] = value
                        used_keys.append(token.key)
                        available_keys.remove(token.key)
                    else:
                        if value != token_dict[token.key]:
                            raise ValueError ('Path contains diffent values for token key: %s' % (token.key))
                    #print ('VALUES:', values)
                    #print ('TOKENS: ', tokens)

        if not set(self.keys_non_optional).issubset(set(used_keys)):
            raise KeyError ('Missing keys in path. Used keys: %s\nRequired token keys: %s'
                            % (used_keys, (self.keys_non_optional)))
        return token_dict

    def url_to_dict(self, path_str) -> list:
        pass

    def path_from_dict(self, token_dict=None) -> str:
        errors = []
        if not token_dict:
            token_dict = {}
        path = self.anchor
        for token in self.token_list_flattened:
            if token.is_constant:
                path += token.path
            else:
                if token.key in token_dict.keys():
                    path += token.path_from_str(str(token_dict[token.key]))
                else:
                    if not token.is_optional:
                        error = f"Unable to create path from token_dict. \
Missing token.key: {token.key} in dict: {token_dict}"
                        errors.append(error)
        if len(errors):
            for error in errors:
                print (error)
                logging.critical(error)
            raise KeyError (str(errors))
        return path
    
    def dict_to_url(self, token_dict) -> str:
        pass

    def _pretokens_from_path(self, path='') -> list:
        """Return pre-tokens/components of a path

        Intermediate process creates a list of pre-tokens/components
        from schema string.

        Args:
            path (str): File system token structure.

        Returns:
            list: of strings that can be used to create tokens

        Example:
            >>> '\\{@show}{\\@sequence}{/@shot}/{#product}{_@variable}'
            >>> is returned as:
            >>> ['/@show', '/@sequence', '/@show', '/#product']
        Note the change in folder delimeters. The method attempts to repair some
        common syntax errors in building a schema.
        """

        matches = re.findall(K.TOKEN_MATCH_BRACES, path)
        matched_components = []
        filtered_components = []
        for match in matches:
            match_str = match[0] if match[0] else match[1]
            match_str = match_str.replace('?','') + '?' if '?' in match_str else match_str
            matched_components.append(match_str)
        prepend = True
        for component in matched_components:
            if component.count('/') > 1:
                for s in component.split('/'):
                    if s != '':
                        prepend = True
                        filtered_components.append('/'+s)
            else:
                if component == '/':
                    prepend = True
                else:
                    if '/' in component:
                        component = '/'+component.replace('/', '')
                    elif prepend:
                        component = '/'+component
                    filtered_components.append(component)
                    prepend = False
        '''logging.debug('call _pretokens_from_path(%s)\nPATH COMPONENTS: %s\n'
                      ,self, filtered_components)'''
        return filtered_components

    def _tokens_from_components(self, components=None) -> list:
        if components is None:
            components = []
        tokens = []
        for component in components:
            try:
                token = Token(component)
                if token:
                    tokens.append(token)
            except Exception as e:
                self._errors.append(e)
        '''logging.debug('call _tokens_from_components(%s)\nTOKENS: %s\n'
                    ,self, tokens)'''
        return tokens

    def _group_tokens(self, tokens=None) -> list:
        if tokens is None:
            tokens = []
        dels = K.DELIMETERS
        path_groupings = []
        level1_list = []
        level2_list = []
        level1_optional_count = 0
        level2_optional_count = 0
        previous_delimeter = dels[2]
        error_str = 'call _group_components({})\n\
Too many optional tokens at delimeter level: "{}"\n'

        while tokens:
            token = tokens.pop()
            if token.delimeter != previous_delimeter:
                if previous_delimeter == dels[2]:
                    copy_list = level2_list
                    level1_list.insert(0, copy_list)
                    level2_list = []
                    if level2_optional_count > 1:
                        error_str = error_str.format(self, dels[2])
                        self._errors.append(error_str)
                        logging.warning(error_str)
                        raise RecursionError(error_str)
                    else:
                        level1_optional_count = 0
                        level2_optional_count = 0
            level2_list.insert(0, token)
            if token.delimeter == dels[0]:
                copy_list = level2_list
                level1_list.insert(0, copy_list)
                level2_list = []

                copy_list = level1_list
                path_groupings.insert(0, copy_list)
                level1_list = []
                if level1_optional_count > 1\
                or (level1_optional_count > 0
                and K.ALLOW_MULTIDELIMITED_TOKEN):
                    error_str = error_str.format(self, dels[1])
                    self._errors.append(error_str)
                    logging.warning(error_str)
                    raise RecursionError(error_str)
                else:
                    level1_optional_count = 0
                    level2_optional_count = 0
            else:
                if token.is_optional:
                    level1_optional_count += 1
                    level2_optional_count += 1
            previous_delimeter = token.delimeter
        '''logging.debug('call _group_tokens(%s)\nTOKEN GROUPINGS: %s\n'
                    ,self, path_groupings)'''
        return path_groupings

    def _validate(self) -> None:
        self._errors = []
        components = self._pretokens_from_path(path=self.unanchored_path)
        tokens = self._tokens_from_components(components=components)
        self._tokens_list = self._group_tokens(tokens=tokens)