import re

class BasqueStemmer:
    def __init__(self):
        # Define vowels and non-vowels (for RV marking)
        self.vowels = 'aeiou'
        self.non_vowels = 'bcdfghjklmnpqrtstvwxyz'
        
        # Define suffixes for verbs (aditzak), nouns (izenak), and adjectives (adjetiboak)
        self.verbs_suffixes = [
            'le', 'la', 'tzaile', 'aldatu', 'atu', 'tzailea', 'taile', 'tailea', 'pera', 'gale', 'galea', 'gura', 
            'kura', 'kor', 'korra', 'or', 'orra', 'tun', 'tuna', 'gaitz', 'gaitza', 'kaitz', 'kaitza', 'ezin', 'ezina',
            'tezin', 'tezina', 'errez', 'erreza', 'karri', 'karria', 'tzaga', 'tzaka', 'tzake', 'tzeke', 'ez', 'eza',
            'tzez', 'keta', 'eta', 'etan', 'pen', 'pena', 'tze', 'atze', 'kuntza', 'kunde', 'kundea', 'kune', 'kunea', 
            'kuna', 'kera', 'era', 'kizun', 'kizuna', 'dura', 'tura', 'men', 'mena', 'go', 'ago', 'tio', 'taldi', 'taldia',
            'aldi', 'aldia', 'gune', 'gunea', 'bide', 'bidea', 'pide', 'pidea', 'gai', 'gaia', 'ki', 'kin', 'ekin','rekin', 'kina',
            'kari', 'karia', 'ari', 'tari', 'etari', 'gailu', 'gailua', 'kide', 'kidea', 'ide', 'idea', 'du', 'ka', 'kan', 
            'an', 'ean', 'tu', 'lari', 'tatu', 'rean', 'tarazi', 'arazi', 'tzat', 'bera', 'dako', 'garri', 'garria', 'tza'
        ]
        
        self.nouns_suffixes = [
            'ari', 'aria', 'bizia', 'kari', 'karia', 'lari', 'laria', 'tari', 'taria', 'zain', 'zaina', 'tzain', 'tzaina',
            'zale', 'zalea', 'tzale', 'tzalea', 'aizun', 'orde', 'ordea', 'burua', 'ohi', 'ohia', 'kintza', 'gintzo', 'gintzu',
            'tzu', 'tzua', 'tzo', 'tzoa', 'kuntza', 'talde', 'taldea', 'eria', 'keria', 'teria', 'di', 'za', 'ada', 'tara',
            'etara', 'tra', 'ta', 'tegi', 'tegia', 'keta', 'z', 'zko', 'zkoa', 'ti', 'tia', 'tsu', 'tsua', 'zu', 'zua', 'bera',
            'pera', 'zto', 'ztoa', 'asi', 'asia', 'gile', 'gilea', 'estu', 'estua', 'larri', 'larria', 'nahi', 'nahia', 'koi',
            'koia', 'oia', 'goi', 'min', 'mina', 'dun', 'duna', 'duru', 'durua', 'duri', 'duria', 'os', 'osa', 'oso',
            'osoa', 'ar', 'ara', 'tar', 'dar', 'dara', 'tiar', 'tiara', 'liar', 'liara', 'gabe', 'gabea', 'kabe', 'kabea',
            'ga', 'ge', 'kada', 'tasun', 'tasuna', 'asun', 'asuna', 'go', 'mendu', 'mendua', 'mentu', 'mentua', 'mendi',
            'mendia', 'zio', 'zioa', 'zino', 'zinoa', 'zione', 'zionea', 'ezia', 'degi', 'degia', 'egi', 'egia', 'toki', 
            'tokia', 'leku', 'lekua', 'gintza', 'alde', 'aldea', 'kalde', 'kaldea', 'gune', 'gunea', 'une', 'unea', 'una',
            'pe', 'pea', 'gibel', 'gibela', 'ondo', 'ondoa', 'arte', 'artea', 'aurre', 'aurrea', 'etxe', 'etxea', 'ola',
            'ontzi', 'ontzia', 'gela', 'denda', 'taldi', 'taldia', 'aldi', 'aldia', 'te', 'tea', 'zaro', 'zaroa', 'taro',
            'taroa', 'oro', 'oroa', 'aro', 'aroa', 'ero', 'eroa', 'eroz', 'eroza',  'kan', 'kana', 'tako', 'etako',
            'takoa', 'kote', 'kotea', 'tzar', 'tzarra', 'handi', 'handia', 'kondo', 'kondoa', 'skila'
        ]
        
        self.adjectives_suffixes = [
            'era', 'ero', 'go', 'tate', 'tade', 'date', 'dade', 'keria', 'ki', 'to', 'ro', 'la', 'gi', 'larik', 'lanik', 'ik',
            'ztik', 'rik', 'zlea', 'z'
        ]
        
        self.plural_suffixes = ['ak', 'ek','k']
    
    def mark_regions(self, word):
        print(word)
        # RV, R1, R2 marking procedure
        pV, p1, p2 = len(word), len(word), len(word)
        print(len(word))
        
        # Mark the position of the first vowel (pV)
        for i in range(len(word)):
            if word[i] in self.vowels:
                pV = i
                break
        print(f"Pos: {pV} {word[pV]}")
        
        # Mark the regions R1 and R2
        for i in range(pV, len(word)):
            if word[i] in self.non_vowels:
                p1 = i
                break
        print(f"Pos: {p1} {word[p1]}")
        
        for i in range(p1, len(word)):
            if word[i] in self.vowels: #and word[i+1] in self.non_vowels:
                p2 = i
                break
        print(f"Pos: {p2} {word[p2]}")
                
        return pV, p1, p2

    def remove_plural_suffix(self, word, suffixes):
        print(word)
        # Recorrer la lista de sufijos y eliminar el que coincida con el final de la palabra
        for suffix in suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)]  # Eliminar el sufijo encontrado
        return word  # Si no se encuentra ningún sufijo, devolver la palabra original

    
    def remove_consonants_until_vowel(self, word):
       
        # Convert the word into a list to mutate it
        word = list(word)

        # Start iterating from the second last character to the beginning
        for idx in range(len(word) - 1, 0, -1):
            # If the current character is a vowel return the word
            if word[idx] in self.vowels:
                break               
            # If the current character is a consonant and the next one is also a consonant
            elif word[idx] in self.non_vowels and word[idx - 1] in self.non_vowels:
                word.pop(idx)  # Remove the current consonant
            # If the next character is a vowel, stop removing consonants
            elif word[idx - 1] in self.vowels:
                word.pop(idx)
                break

        return ''.join(word)
    
    def apply_suffixes(self, word, suffixes, region):
        pV, p1, p2 = region
        # Remove suffixes from the word based on rules
        for suffix in suffixes:            
            if word.endswith(suffix):
                print(suffix)
                if p2 <= len(word) and word.endswith(suffix):
                    return word[:-(len(suffix)-1)]
        return word
    
    def stem(self, word):
        # Step 1: Mark regions
        pV, p1, p2 = self.mark_regions(word)
        
        # Step 2: Apply rules for verbs, nouns, and adjectives
        word = self.apply_suffixes(word, self.verbs_suffixes, (pV, p1, p2))
        word = self.apply_suffixes(word, self.nouns_suffixes, (pV, p1, p2))
        word = self.apply_suffixes(word, self.adjectives_suffixes, (pV, p1, p2))
        
        # Step 3: Apply singularization 
        word = self.remove_plural_suffix(word, self.plural_suffixes)   

        word = self.remove_consonants_until_vowel(word)       
        
        return word

# Example usage:
stemmer = BasqueStemmer()
for recipe in recipe_list:
    words = recipe.split(" ")
    print(words)    
    stemmed_words = [stemmer.stem(word) for word in words]
    print("konponduta: ", stemmed_words)
    input()


print(stemmed_words)
