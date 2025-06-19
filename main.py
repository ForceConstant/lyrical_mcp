# server.py
from mcp.server.fastmcp import FastMCP
import nltk
from nltk.corpus import cmudict
import re


nltk.download('cmudict')
nltk.download('punkt_tab')

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
def count_syllables(input_string: str) -> list[int]:
    """
    Counts the number of syllables in each line of the input string.
    Utilizes nltk's CMU Pronouncing Dictionary.
    """
    d = cmudict.dict()
    syllable_counts = []
    lines = input_string.splitlines()

    for line in lines:
        words = nltk.word_tokenize(line.lower())
        line_syllables = 0
        for word in words:
            if word in d:
                # Take the first pronunciation and count vowels
                # A common heuristic for syllable counting in CMUDict is to count the number of vowels
                # in the pronunciation. Each vowel sound typically corresponds to a syllable.
                # This is a simplification, but often effective.
                pronunciation = d[word][0]
                syllables = [s for s in pronunciation if s[-1].isdigit()]
                line_syllables += len(syllables)
            else:
                # Fallback for words not in dictionary: simple vowel count
                line_syllables += sum(1 for char in word if char in "aeiouy")
        syllable_counts.append(line_syllables)
    return syllable_counts


@mcp.tool()
def find_rhymes(input_word: str) -> dict[str, list[str]]:
    """
    Finds rhyming words for a given input word, categorized by syllable count (1, 2, or 3 syllables).
    Utilizes nltk's CMU Pronouncing Dictionary.
    """
    d = cmudict.dict()
    input_word_lower = input_word.lower()

    if input_word_lower not in d:
        return {"error": f"'{input_word}' not found in dictionary. Cannot find rhymes."}

    # Get pronunciations for the input word
    input_pronunciations = d[input_word_lower]

    rhymes = {
        "1_syllable": [],
        "2_syllable": [],
        "3_syllable": []
    }

    for input_pron in input_pronunciations:
        # Find the primary stress vowel (usually indicated by '1' or '2' after the vowel sound)
        # and the sounds that follow it.
        # This is a common heuristic for identifying the rhyming part of a word.
        rhyme_part_index = -1
        for i, phoneme in enumerate(input_pron):
            if re.match(r'[AEIOU].*[12]', phoneme): # Matches vowel sounds with primary or secondary stress
                rhyme_part_index = i
                break
        
        if rhyme_part_index == -1:
            continue # No stressed vowel found, skip this pronunciation

        rhyme_part = input_pron[rhyme_part_index:]

        for word, pronunciations in d.items():
            if word == input_word_lower:
                continue # Don't include the input word itself

            for pron in pronunciations:
                # Check if the word's pronunciation ends with the rhyme_part
                if len(pron) >= len(rhyme_part) and pron[-len(rhyme_part):] == rhyme_part:
                    # Count syllables for the rhyming word
                    syllables = [s for s in pron if s[-1].isdigit()]
                    syllable_count = len(syllables)

                    if syllable_count == 1 and word not in rhymes["1_syllable"]:
                        rhymes["1_syllable"].append(word)
                    elif syllable_count == 2 and word not in rhymes["2_syllable"]:
                        rhymes["2_syllable"].append(word)
                    elif syllable_count == 3 and word not in rhymes["3_syllable"]:
                        rhymes["3_syllable"].append(word)
    
    # Limit to 10-20 rhymes per category if many are found
    for key in rhymes:
        rhymes[key] = rhymes[key][:20] # Take up to 20, can be less

    return rhymes


if __name__ == "__main__":
    mcp.run(transport="streamable-http")