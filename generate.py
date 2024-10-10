"""
This will take a CSV file exported from mtgarena.pro (e.g. your collection) and a bulk export from Scryfall, then add details
about your collection in a fresh JSON file. You can then give this JSON file to an AI like ChatGPT to help strategically generate
new decks.

1. Download a complete Scryfall export of Oracle cards.
2. Place the file in the same directory as this script and name it `oracle-cards.json`
3. Export your collection from mtgarena.pro (goldfish format).
4. Place the file in the same directory as this script and name it `collection.csv`
5. Run the script with python generate.py -v

You can also generate a smaller file 
"""
import argparse
import csv
import json
import re
import unicodedata
import os


# Specify colors
colors = [
    "B", # black
    "W", # white
    "R", # red
    "U", # blue (underwater)
    "G", # green,
    "N", # colorless (neutral)
]

# Specify the formats to include in legalities
formats = [
    "standard",
    "alchemy",
    "brawl",
    "standardbrawl"
]

# Parse command-line arguments for the format
parser = argparse.ArgumentParser(description="Turn your goldfish format collection into a detailed JSON file for AI parsing.")
parser.add_argument("--format", type=str, help="Format to filter by (e.g. standard, alchemy, brawl, or standardbrawl)")
parser.add_argument("--colors", nargs='+', type=str, help="Only include cards that include one or more specified colors (e.g. --colors W B R G U N), note: B=black, U=blue, N=Colorless")
parser.add_argument("--no-colors", nargs='+', type=str, help="Exclude cards that include certain colors (e.g. --colors W B R G U N), note: B=black, U=blue, N=Colorless")
parser.add_argument("-e", action=argparse.BooleanOptionalAction, help="Exclusive color matching. Use with --colors to automatically exclude any not listed.")
parser.add_argument("-v", action=argparse.BooleanOptionalAction, help="Output information to the terminal as the script runs.")
args = parser.parse_args()

# Automatically populate --no-colors if both --colors and -e are provided
if args.colors and args.e:
    # Calculate colors not mentioned in --colors
    args.no_colors = [color for color in colors if color not in args.colors]
    
    if args.v:
        print(f"Excluding colors: {', '.join(args.no_colors)}")

# Count the number of cards we process
output_count=0

# Keep track of the USD value
usd_value=0.00

# If a format is passed, ensure it's a valid one
if args.format and args.format not in formats:
    raise ValueError(f"Invalid format '{args.format}'. Valid formats are: {', '.join(formats)}")

# Load JSON data from Scryfall
with open('oracle-cards.json', 'r', encoding='utf-8') as json_file:
    cards_data = json.load(json_file)

# Load CSV data from mtgarena.pro collection export
with open('collection.csv', 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    cards_csv = list(csv_reader)

# Create a list to store the output
output_data = []


def normalize_text(text):
    """Normalize the names by removing accents (mtgarena.pro includes pre-normalized names)"""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def find_matching_card(card_name, cards_data):
    """Match card names (mtgarena and scryfall use different naming conventions)"""
    # Normalize the card name from CSV
    normalized_card_name = normalize_text(card_name)
    
    # Create a regex pattern to match the normalized card_name followed by " // " and anything else
    pattern = re.compile(r'^' + re.escape(normalized_card_name) + r'( // .*)?$')
    
    for item in cards_data:
        # Normalize the JSON card name
        normalized_json_name = normalize_text(item['name'])
        
        # Check if the normalized JSON card name matches the pattern
        if pattern.match(normalized_json_name):
            return item
    return None

# Iterate over each card in the CSV
for card in cards_csv:
    card_name = card['Card']
    matching_card = find_matching_card(card_name, cards_data)
    
    # If a matching card is found in the JSON
    if matching_card:
        # Filter legalities: include only ones in our supported list and replace string values to keep output shorter
        filtered_legalities = {
            k: 1 if v == 'legal' else 0
            for k, v in matching_card.get('legalities', {}).items()
            if k in formats
        }
        
        # If a format argument is passed, check legality for that format
        if args.format:
            # Skip cards not legal in the given format
            if filtered_legalities.get(args.format) != 1:
                if args.v:
                    print(f"-- Omitting {card_name} because it is not legal in {args.format}")
                continue

        # Filter cards by colors if the --colors argument is provided
        if args.colors:
            card_colors = matching_card.get('colors', [])
            # Colorless cards need special handling
            if ('N' in args.colors and not card_colors) or any(color in card_colors for color in args.colors if color != 'N'):
                pass  # The card passes
            else:
                if args.v:
                    print(f"-- Omitting {card_name} because it does not include any specified colors.")
                continue

        # Exclude cards by colors if the --no-colors argument is provided
        if args.no_colors:
            exclude_colors = matching_card.get('colors', [])
            # Colorless cards still need special handling
            if ('N' in args.no_colors and not exclude_colors) or any(color in exclude_colors for color in args.no_colors if color != 'N'):
                if args.v:
                    print(f"-- Excluding {card_name} because it includes an excluded color.")
                continue

        # Calculate total value based on card price (if exists)
        try:
            card_price = matching_card.get('prices', {}).get('usd')
            if card_price is not None:
                quantity = int(card['Quantity'])
                usd_value += float(card_price) * quantity
        except:
            pass

        # Exclude basic lands
        type = matching_card.get('type_line', '')
        if "Basic Land" in type:
                if args.v:
                    print(f"-- Omitting {card_name} because it is a basic land.")
                continue
        
        card_data = {
            'name': card_name,
            #'set_name': card['Set Name'],
            #'release_date': matching_card.get('released_at', ''),
            'type': type,
            'cost': matching_card.get('mana_cost', ''),
            'text': matching_card.get('oracle_text', ''),
            'qty': card['Quantity']
        }

        # Make these things optional to limit file size
        keyw = matching_card.get('keywords', [])
        if keyw:
            card_data['keyw'] = keyw

        pow = matching_card.get('power', '')
        if pow:
            card_data['tough'] = pow

        tough = matching_card.get('toughness', '')
        if tough:
            card_data['tough'] = tough


        if not args.format:
            # Create a list of keys from filtered_legalities that have values of 1
            legal_for = [k for k, v in filtered_legalities.items() if v == 1]
            card_data['legal_for'] = legal_for

        if args.v:
            print(f"Added {card_name}")

        # Add the data
        output_count += 1
        output_data.append(card_data)
    else:
        print(f"Unable to find match for {card_name}!")

# Build the file output name
output_file = 'output/'

if args.format:
    output_file += f'format-{args.format}'
else:
    output_file += 'formats-all'

# Included colors?
if args.colors:
    included_colors_str = '-'.join(args.colors)
    output_file += f'.include-{included_colors_str}'

# Excluded colors?
if args.no_colors:
    excluded_colors_str = '-'.join(args.no_colors)
    output_file += f'.exclude-{excluded_colors_str}'

# Add extension
output_file += '.json'

# Ensure the output directory exists
output_dir = os.path.dirname(output_file)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)  # Creates the directory if it doesn't exist

# Write the output data to a JSON file
with open(output_file, 'w', encoding='utf-8') as json_output_file:
    #json.dump(output_data, json_output_file, indent=4)
    json.dump(output_data, json_output_file)

print(f"Output for {output_count} cards written to {output_file}")
print(f"The paper value of processed cards is ${usd_value:.2f}")
