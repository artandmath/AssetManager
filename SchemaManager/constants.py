"""Define all constant variables here."""

HIDDEN_CHAR = '#'
EDITABLE_CHAR = '@'
OPTIONAL_CHAR = '?'
TOKEN_MATCH_BRACES = r'\{(.*?)\}|([^{]+)'
VERSION_MATCH_BRACES = r'([^[]+)\[([^\]]+)\]'

SCHEMA_STYLE = 0
match SCHEMA_STYLE:
    case 0:
        # Style: CapiTilizAtioN alphanumeric and '-' allowed in token values
        # Delimitered by '_' and '_' not allowed in token values
        # Allow an optional token key and arbitary placement of version tokens
        DELIMETERS = ['/', '_', '.']
        TOKEN_KEY_MATCH = r'^[a-zA-Z0-9.]+$'
        TOKEN_VALUE_MAP = r'^[a-zA-Z0-9-]+$'
        ALLOW_MULTIDELIMITED_TOKEN = False

    case 1:
        # Style: lowercase alphanumeric and '-' allowed in token values
        # Delimitered by '_' and '_' not allowed in token values
        # Allow an optional token key and arbitary placement of version tokens
        DELIMETERS = ['/', '_', '.']
        TOKEN_KEY_MATCH = r'^[a-zA-Z0-9.]+$'
        TOKEN_VALUE_MAP = r'^[a-z0-9-]+$'
        ALLOW_MULTIDELIMITED_TOKEN = False

    case 2:
        # Style: CapiTilizAtioN alphanumeric and '_' allowed in token values
        # Delimitered by '-' and '-' not allowed in token values
        # Allow an optional token key and arbitary placement of version tokens
        DELIMETERS = ['/', '-', '.']
        TOKEN_KEY_MATCH = r'^[a-zA-Z0-9.]+$'
        TOKEN_VALUE_MAP = r'^[a-zA-Z0-9_]+$'
        ALLOW_MULTIDELIMITED_TOKEN = False

    case 3:
        # Style: lowercase alphanumeric and '_' allowed in token values
        # Delimitered by '-' and '-' not allowed in token values
        # Allow an optional token key and arbitary placement of version tokens
        DELIMETERS = ['/', '-', '.']
        TOKEN_KEY_MATCH = r'^[a-zA-Z0-9.]+$'
        TOKEN_VALUE_MAP = r'^[a-z0-9_]+$'
        ALLOW_MULTIDELIMITED_TOKEN = False
