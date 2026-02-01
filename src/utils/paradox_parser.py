import re
from typing import Dict, List, Any, Union

class ParadoxToken:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line})"

class ParadoxParser:
    """
    Tokenizer and parser for Paradox script format (nested braces).
    Handles: key = value, key = { ... }, lists, and comments.
    """
    
    def __init__(self):
        self.tokens = []
        self.pos = 0
        
    def tokenize(self, text: str) -> List[ParadoxToken]:
        """Splits text into a stream of tokens."""
        tokens = []
        line_num = 1
        i = 0
        length = len(text)
        
        while i < length:
            char = text[i]
            
            # Whitespace
            if char.isspace():
                if char == '\n':
                    line_num += 1
                i += 1
                continue
                
            # Comments
            if char == '#':
                while i < length and text[i] != '\n':
                    i += 1
                continue
                
            # Operators and Delimiters
            if char in '{}= "':
                if char == '"':
                    # String literal
                    start = i + 1
                    i += 1
                    while i < length and text[i] != '"':
                        if text[i] == '\\' and i+1 < length and text[i+1] == '"':
                            i += 2
                        else:
                            i += 1
                    tokens.append(ParadoxToken('STRING', text[start:i], line_num))
                    i += 1 # Skip closing quote
                elif char == '{':
                    tokens.append(ParadoxToken('LBRACE', '{', line_num))
                    i += 1
                elif char == '}':
                    tokens.append(ParadoxToken('RBRACE', '}', line_num))
                    i += 1
                elif char == '=':
                    tokens.append(ParadoxToken('EQUALS', '=', line_num))
                    i += 1
                continue
                
            # Identifiers and Numbers (unquoted strings)
            start = i
            while i < length and not text[i].isspace() and text[i] not in '{}=#"':
                i += 1
            value = text[start:i]
            if value:
                tokens.append(ParadoxToken('IDENTIFIER', value, line_num))
                
        return tokens

    def parse_tokens(self, tokens: List[ParadoxToken]) -> Dict[str, Any]:
        """Parses a list of tokens into a nested dictionary structure."""
        self.tokens = tokens
        self.pos = 0
        result = {}
        
        while self.pos < len(self.tokens):
            if self.tokens[self.pos].type == 'RBRACE':
                break
                
            key = self._parse_key()
            if not key:
                break
                
            # Check for assignment
            if self.pos < len(self.tokens) and self.tokens[self.pos].type == 'EQUALS':
                self.pos += 1 # Skip '='
                value = self._parse_value()
                
                # Handle duplicate keys (common in Paradox scripts, e.g. multiple 'component_slot')
                if key in result:
                    if not isinstance(result[key], list):
                        result[key] = [result[key]]
                    result[key].append(value)
                else:
                    result[key] = value
            else:
                # Key without value (e.g. in a list: { a b c })
                # Return list mode? For now, assume key=value structure dominant in root
                # If we are inside a list block, _parse_value handles it.
                # But at root level, standalone keys are rare unless it's a list file.
                pass
                
        return result

    def _parse_key(self) -> Union[str, None]:
        if self.pos >= len(self.tokens):
            return None
        token = self.tokens[self.pos]
        self.pos += 1
        return token.value

    def _parse_value(self) -> Any:
        if self.pos >= len(self.tokens):
            return None
            
        token = self.tokens[self.pos]
        
        if token.type == 'LBRACE':
            self.pos += 1
            # Check if it's a list or dict
            # Lookahead specifically for identifier followed by equals?
            # Or just parse as dict and if keys are indices, convert?
            # Paradox "lists" are just values separated by whitespace inside braces
            
            values = []
            dict_data = {}
            is_dict = False
            
            while self.pos < len(self.tokens) and self.tokens[self.pos].type != 'RBRACE':
                # Lookahead
                if self.pos + 1 < len(self.tokens) and self.tokens[self.pos+1].type == 'EQUALS':
                    is_dict = True
                    k = self._parse_key()
                    self.pos += 1 # Skip =
                    v = self._parse_value()
                    # Handle dupes
                    if k in dict_data:
                        if not isinstance(dict_data[k], list):
                            dict_data[k] = [dict_data[k]]
                        dict_data[k].append(v)
                    else:
                        dict_data[k] = v
                else:
                    # List item
                    val = self._parse_value()
                    values.append(val)
            
            self.pos += 1 # Skip RBRACE
            
            if is_dict:
                # If we had mixed dict/list, Paradox usually treats them as fields. 
                # If 'values' has items, they might be dropped or stored in special key?
                # For now return dict if any KV pair found.
                return dict_data
            else:
                return values
                
        elif token.type in ('STRING', 'IDENTIFIER'):
            self.pos += 1
            # Try convert to number
            try:
                if '.' in token.value:
                    return float(token.value)
                else:
                    return int(token.value)
            except ValueError:
                # Boolean?
                if token.value == 'yes': return True
                if token.value == 'no': return False
                # Remove quotes if string
                return token.value.strip('"')
                
        return None

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Reads and parses a file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        tokens = self.tokenize(text)
        return self.parse_tokens(tokens)

    def parse_block(self, text: str) -> Dict[str, Any]:
        """Parses a raw text block."""
        tokens = self.tokenize(text)
        return self.parse_tokens(tokens)
