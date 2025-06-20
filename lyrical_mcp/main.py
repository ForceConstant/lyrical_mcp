from typing import Dict, Any
import os
import re

# Lazy loading to prevent tool scanning timeouts
def get_mcp():
    """Lazy-loaded FastMCP instance to avoid import-time dependencies."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("lyrical-mcp")

def get_nltk_dependencies():
    """Lazy-loaded NLTK dependencies."""
    import nltk
    from nltk.corpus import cmudict
    return nltk, cmudict

def setup_tools(mcp):
    """Setup tools on the MCP server instance."""

    @mcp.tool()
    async def ping() -> str:
        """Simple ping tool to test server responsiveness and prevent timeouts."""
        return "pong"

    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """Health check to verify server connectivity and status."""
        from datetime import datetime
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server": "lyrical-mcp",
            "version": "1.0.0",
            "tools_available": ["ping", "health_check", "count_syllables", "find_rhymes"]
        }

    @mcp.tool()
    def count_syllables(input_string: str) -> list[int]:
        """
        Counts the number of syllables in each line of the input string.
        Utilizes nltk's CMU Pronouncing Dictionary.
        """
        nltk, cmudict = get_nltk_dependencies()
        d = cmudict.dict()
        syllable_counts = []
        lines = input_string.splitlines()

        for line in lines:
            words = nltk.word_tokenize(line.lower())
            line_syllables = 0
            for word in words:
                if word in d:
                    pronunciation = d[word][0]
                    syllables = [s for s in pronunciation if s[-1].isdigit()]
                    line_syllables += len(syllables)
                else:
                    line_syllables += sum(1 for char in word if char in "aeiouy")
            syllable_counts.append(line_syllables)
        return syllable_counts

    @mcp.tool()
    def find_rhymes(input_word: str) -> dict[str, list[str]]:
        """
        Finds rhyming words for a given input word, categorized by syllable count (1, 2, or 3 syllables).
        Utilizes nltk's CMU Pronouncing Dictionary.
        """
        nltk, cmudict = get_nltk_dependencies()
        d = cmudict.dict()
        input_word_lower = input_word.lower()

        if input_word_lower not in d:
            return {"error": f"'{input_word}' not found in dictionary. Cannot find rhymes."}

        input_pronunciations = d[input_word_lower]

        rhymes = {
            "1_syllable": [],
            "2_syllable": [],
            "3_syllable": []
        }

        for input_pron in input_pronunciations:
            rhyme_part_index = -1
            for i, phoneme in enumerate(input_pron):
                if re.match(r'[AEIOU].*[12]', phoneme):
                    rhyme_part_index = i
                    break
            
            if rhyme_part_index == -1:
                continue

            rhyme_part = input_pron[rhyme_part_index:]

            for word, pronunciations in d.items():
                if word == input_word_lower:
                    continue

                for pron in pronunciations:
                    if len(pron) >= len(rhyme_part) and pron[-len(rhyme_part):] == rhyme_part:
                        syllables = [s for s in pron if s[-1].isdigit()]
                        syllable_count = len(syllables)

                        if syllable_count == 1 and word not in rhymes["1_syllable"]:
                            rhymes["1_syllable"].append(word)
                        elif syllable_count == 2 and word not in rhymes["2_syllable"]:
                            rhymes["2_syllable"].append(word)
                        elif syllable_count == 3 and word not in rhymes["3_syllable"]:
                            rhymes["3_syllable"].append(word)
        
        for key in rhymes:
            rhymes[key] = rhymes[key][:20]

        return rhymes

def main():
    """Main entry point for the syllables MCP server."""
    mcp = get_mcp()
    setup_tools(mcp)
    
    print("🌐 Starting lyrical MCP server")
    mcp.run()

if __name__ == "__main__":
    main()