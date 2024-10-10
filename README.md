# MtG AI Deck Generation Prep
This CLI-based script takes your goldfish-format collection export from mtgarena.pro (or similar) and combines it with data from scryfall.com to create a small-as-possible JSON file that can be fed to AI for deck generation tips.

1. Place your `collection.csv` file in the same directory as generator.py (this is what you might download from mtgarena.pro)
2. Place the "Default Cards" dataset from scryfall and place it in the same directory as generator.py. Name this file `oracle-cards.json`
3. Run `python generator.py` to generate a complete collection.

## Quirks
Be aware that complete collections are too much data for most AI tools (like ChatGPT). So the CLI provides options for making the datasets smaller. You can specify a specific format, specific colors to include, and specific colors to exclude.

Basic lands are also automatically left out of generated data to keep the sets as small as possible.

A command like this works well:
```bash
python generate.py --format standard --colors B G N --no-colors U W R
```

Feed to ChatGPT with a prompt like...

```
I am giving you a JSON dataset containing Black, Green, and Colorless cards in my MtG Arena collection. Look at whats available, create a deck strategy, and then give me an exact 60 card deck I can make from what is in this data set. Keep in mind that basic land cards are available, even though they aren't in the file.
---
YOUR JSON HERE
```

## Color references:
B = Black  
U = Blue (think "Underwater")  
G = Green  
R = Red  
W = White  
N = Colorless (No Color)  
