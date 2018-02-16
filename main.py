"""
Simple Python 3.x HTML web scraping example using 'requests' and 'Beautiful Soup 4' modules.
Scrapes popular Pokémon database/wiki site Bulbapedia (https://bulbapedia.bulbagarden.net)
for Pokémon in-game locations and prints them to the console ordered by Generation.

Author: Kennedy Owen
"""

from sys import exit
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup, NavigableString
from gen_table import GenTable


def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def get_pokemon_page(poke_name):
    """
    Given a Pokémon's name (e.g. 'Pikachu'), request that Pokémon's page content from
    the Bulbapedia site.
    """
    try:
        url = "http://bulbapedia.bulbagarden.net/wiki/" + poke_name + "_(Pokémon)"
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        print('Error during page request for Pokémon {0} : {1}'.format(poke_name, str(e)))


def get_generation_tables(inner_tables, gen_tables_elem):
    """
    Given the outermost game locations table element, parse each 'Generation' table
    within for easier game and locations parsing.
    """
    # Find first inner (generation) table
    gen_tr_pointer = gen_tables_elem.find("tr")

    # Accumulate each generation table
    while gen_tr_pointer is not None:
        first_inner_td = gen_tr_pointer.find("td")
        if first_inner_td is not None:
            inner_gen_table = first_inner_td.find("table")
            if inner_gen_table is not None:
                inner_tables.append(inner_gen_table)
        gen_tr_pointer = gen_tr_pointer.find_next_sibling("tr")


def parse_loc_string(loc):
    """
    Given a game-specific location pointer in bs4 page format, parse the string found
    within it (recursively if the element contains embedded children with multiple
    strings) and return it.
    """
    # Not plain string
    if type(loc) is not NavigableString:
        # Found superscript
        if loc.find("sup") is not None:
            return " [" + "".join(loc.strings) + "]"
        # Found embedded string
        elif loc.name == "small":
            embedded_parsed_string = ""
            for embedded_loc in loc.children:
                embedded_parsed_string += parse_loc_string(embedded_loc)
            return embedded_parsed_string
        # Found asterisk/"explain"
        elif loc.get('class') is not None and loc.get('class')[0] == 'explain':
            return " {" + loc.get('title') + "}"
        # Found <br> element
        elif loc.name == "br":
            return ", "
        # Found hyperlink, etc.
        else:
            return "".join(loc.strings)
    # Found plain string
    else:
        return loc.string


def print_locations_table(page_contents):
    """
    Given raw page request HTML from a Bulbapedia Pokémon page, parse it using Beautiful
    Soup 4 and retrieve all necessary Pokémon location data from the HTML to print out later.
    """
    soup = BeautifulSoup(page_contents, 'html.parser')

    # Get Pokémon name and print string
    page_title = soup.find("h1", id="firstHeading").string
    pokemon_name = page_title.split("(Pokémon)")[0].strip()
    locations_string = pokemon_name + " locations:"

    # Check for correct Pokémon page response
    try:
        game_locs_h3 = soup.find(id="Game_locations").parent
    except AttributeError:
        print("Non-legitimate Pokémon " + pokemon_name + ", may be a glitched or ambiguous Pokémon\n")
        return
    table_elem = game_locs_h3.find_next_sibling("table")

    # Parse inner generation tables
    inner_tables = []
    get_generation_tables(inner_tables, table_elem)

    tables_to_print = []

    # Loop over each inner generation table to get games and locations
    for gen_table in inner_tables:
        # Add Generation string
        gen_tr = gen_table.find("tr")
        printable_table = GenTable(gen_tr.find("th").small.string)

        # Skip to next table row, which contains nested games and locs
        games_locs_top_tr = gen_tr.find_next_sibling("tr")

        # Get a pointer to the first game/loc row
        games_locs_table = games_locs_top_tr.find("td").find("table")
        cur_games_locs_tr = games_locs_table.find("tr")

        # Add each Generation's games and associated locations
        while cur_games_locs_tr is not None:
            printable_games = []
            printable_locs = []

            # Add all game names for the current game row (headers)
            headers = cur_games_locs_tr.find_all("th")
            for header in headers:
                printable_games.append(header.find("span").string.strip())

            # Get a pointer to the locations and conditions table for the current game row
            locs_table = cur_games_locs_tr.find("td").find("table")

            # Get a pointer to all locations and conditions strings inside the table
            locs_table_td = locs_table.find("tr").find("td")

            total_string = ""

            # Add all locations and conditions for the current game row
            for loc in locs_table_td.children:
                total_string += parse_loc_string(loc)
            printable_locs.append("".join(total_string).strip())

            # Add new game-loc pair to the table structure
            printable_table.add_game_loc_pair(printable_games, printable_locs)

            # Advance pointer to the next games-locs row
            cur_games_locs_tr = cur_games_locs_tr.find_next_sibling("tr")

        # Add new table with all game-loc pairs to the print array
        tables_to_print.append(printable_table)

    # Print Pokémon name and all game/location parsing results
    print("\n" + locations_string)
    print("=" * len(locations_string))
    for table_to_print in tables_to_print:
        print("")
        table_to_print.print_table()
    print("")


def find_pokemon(pokemon_name):
    """
    Given the name of a Pokémon (e.g. "Pikachu"), scrape all locations and conditions
    in each game the Pokémon appears in from the Pokémon's resulting response page, then
    print out the results.
    """
    # Check for missing entry characters
    if pokemon_name.strip() == "" or pokemon_name is None:
        print("Please enter at least 1 character to search.\n")
        return

    # Fetch response from Pokémon's page on Bulbapedia site
    pokemon_page_contents = get_pokemon_page(pokemon_name)

    # Filter out disambiguation/non-valid page results
    if pokemon_page_contents is None:
        print("Pokémon", pokemon_name, "does not exist! Check for spelling errors"
              " or extra characters and try again.\n")
    # Found a valid Pokémon web page, scrape it and print out all relevant information
    else:
        print_locations_table(pokemon_page_contents)


def start_console():
    print(">Welcome to Pokémon game locations search.")
    print(">Searches website 'https://bulbapedia.bulbagarden.net' for Pokémon game locations.")

    # Prompt user infinitely for requests until program exit
    while True:
        print("")
        pokemon_name = input(">Please enter a Pokémon name, or 'exit' to exit: ")
        if pokemon_name == "exit":
            break
        else:
            find_pokemon(pokemon_name)
    print("\nMay Pokémon RNG be ever in your favor.")
    exit(0)


if __name__ == '__main__':
    start_console()
