class PhonemeEngine:
    def __init__(self):
        # Map letters/sounds to our generated visemes
        self.viseme_map = {
            'a': 'a', 'h': 'a', 'r': 'a',
            'e': 'e', 'i': 'e', 'y': 'e', 's': 'e', 'z': 'e',
            'o': 'o', 'u': 'o', 'w': 'o', 'q': 'o',
            'm': 'm', 'b': 'm', 'p': 'm', 'f': 'm', 'v': 'm',
            ' ': 'idle', '.': 'idle', ',': 'idle', '?': 'idle'
        }

    def get_viseme_for_char(self, char):
        return self.viseme_map.get(char.lower(), 'a') # Default to open mouth for unknown consonants
