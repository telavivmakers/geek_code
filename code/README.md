# Geek Code Decoder

A Python-based decoder for Geek Code 5.x that parses geek code strings and returns their meanings.

## How It Works

The decoder uses regex pattern matching to identify geek codes in a string and looks up their meanings in predefined dictionaries. It handles modifiers (like +++, --, etc) separately from the base codes.

### Example Usage

```python
from geek_decode import parse_geekcode

meaning, remaining = parse_geekcode('GCS++ U+++ Lpy+')
print(meaning)  # Will print meanings with modifiers
print(remaining)  # Will print any unparsed parts of the string
```

## Rules for Adding New Codes

When adding new codes to `codes.py`, follow these guidelines:

1. **Base Codes Only**
   - Add only the base code without modifiers (+++, --, etc)
   - Modifiers are handled separately by the parser
   - Example: For 'U+++', only add 'U' to the dictionary

2. **Code Format**
   - Codes must be distinct words that can be matched with regex word boundaries (\b)
   - Avoid special characters except for common ones like #, !, *
   - Example: 'LC#' for C# is okay, but avoid codes with +, -, @, etc

3. **Dictionary Organization**
   - Group related codes in appropriate dictionaries
   - Each dictionary should focus on one category (e.g., programming_languages, tv_shows)
   - Add clear comments explaining the category

4. **Code Descriptions**
   - Keep descriptions clear and concise
   - Focus on what the code represents, not the modifier meanings
   - Example: 'Unix' instead of 'Unix expert (+++)'

5. **Code Uniqueness**
   - Ensure codes don't conflict across dictionaries
   - Check existing codes before adding new ones
   - If a code could match multiple patterns, use the longer/more specific one first

6. **Documentation**
   - Comment any special cases or considerations
   - Explain category groupings
   - Document any changes to the code format

## Example Dictionary Format

```python
# Category name - brief description of what these codes represent
category_name = {
    'CODE' : 'Clear description',
    'GCS' : 'Geek of Computer Science',
    'LC#' : 'C#',
    # Add more codes...
}
```

## Supported Categories

The decoder currently supports these categories:
- Geek of (professional/academic fields)
- TV Shows
- Programming Languages
- Version Control Systems
- Comics
- Computers
- Politics
- Entertainment
- Lifestyle

## Adding New Categories

To add a new category:

1. Create a new dictionary in `codes.py`
2. Add clear comments explaining the category
3. Follow the code format rules above
4. Add the dictionary to the `dictionaries` list in `parse_geekcode()`

## Testing

When adding new codes, test them with:
```python
python test.py
```

This ensures the parser can correctly identify and decode the new codes.
