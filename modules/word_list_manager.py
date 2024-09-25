import os
import re
import time
import threading
import fcntl, errno
"""
NOTE: If auto_save is True, the word list will be saved to the save_file
every 30 seconds.  This is performed in a separate thread.  For best results,
the stop() method should be called before the program is exited, to ensure
that the thread is stopped and the save_file is saved.
"""

class WordListManager:
    """Manages a list of unique words"""
    def __init__(self, word_list: list[str] = [], save_file: str = None,
                 auto_save: bool = True, inlucde_commonly_misspelled_words: bool = True):
        self.word_list = word_list
        if inlucde_commonly_misspelled_words:
            self.word_list += COMMONLY_MISSPELLED_WORDS

        if save_file is not None:
            self.save_file = os.path.expanduser(save_file)
            self.add_words(self.load_from_file())

        self.auto_save = auto_save
        self.save_interval = 30  # 30 seconds in seconds
        self.stop_event = threading.Event()

        if auto_save:
            self.schedule_save()

    # Schedule the next save
    def schedule_save(self):
        if not self.stop_event.is_set():
            self.save_timer = threading.Timer(self.save_interval, self.save_and_reschedule)
            self.save_timer.daemon = True  # So it doesn't block program exit
            self.save_timer.start()

    # Save the file and then schedule the next save
    def save_and_reschedule(self):
        self.save_to_file()
        self.schedule_save()

    # function to stop the auto-save
    def stop(self):
        self.stop_event.set()
        if hasattr(self, 'save_timer'):
            self.save_timer.cancel()

    # function to load the word_list from a file
    def load_from_file(self):
        if not os.path.exists(self.save_file):
            print(f"File {self.save_file} does not exist.  Skipping load.")
            return []
        with open(self.save_file, 'r') as file:
            word_list = file.read().splitlines()
            word_list = [word.strip() for word in word_list]
        return word_list

    # function to save the word_list to a file
    def save_to_file(self):
        if self.save_file is None:
            return

        lock_file_name = self.save_file + '.lock'
        lock_file = None
        start_time = time.time()
        max_wait_time = 2

        while time.time() - start_time < max_wait_time:
            try:
                lock_file = open(lock_file_name, 'w')
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break  # Lock acquired successfully
            except IOError as e:
                if e.errno != errno.EWOULDBLOCK:
                    raise
                time.sleep(0.1)  # Wait a bit before trying again
        else:
            print(f"Timeout waiting for lock file {lock_file_name}")
            return

        try:
            if not os.path.exists(self.save_file):
                # touch the file if it doesn't exist
                with open(self.save_file, 'w') as file:
                    file.write('')
            existing_words = self.load_from_file()
            self.word_list = list(set(self.word_list + existing_words))

            with open(self.save_file, 'w') as file:
                file.write('\n'.join(self.word_list))
        finally:
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                os.remove(lock_file_name)


    # function to add a word to the word_list
    def add_word(self, word):
        if word not in self.word_list and len(word) >= 3:
            self.word_list.append(word)

    # function to add a list of words to the word_list
    def add_words(self, words):
        for word in words:  # iterate over each word in the list
            self.add_word(word)  # add the word to the word_list

    # function to get the word_list
    def get_word_list(self):
        return self.word_list

    # function to add words from a text string
    def add_words_from_text(self, text: str):
        words = WordListManager.parse_text(text)
        self.add_words(words)

    # Class method to parse text into a list of words
    @classmethod
    def parse_text(cls, text: str) -> list[str]:
        # split the text into words by regex /s+/
        words = re.split(r'[^\w_\-s]+', text)
        # get unique words
        words = list(set(words))
        # filter out words that are too short or too long
        words = [word for word in words if len(word) >= 3]
        return words

# List of correctly spelled words that are often misspelled

COMMONLY_MISSPELLED_WORDS = [
    'abate', 'aberrant', 'abhorrent', 'abscessed', 'abscess', 'absence', 'abundant', 'accessible',
    'accommodate', 'accommodation', 'accompaniment', 'achieve', 'acquaintance', 'acquiesce', 'acquiescence',
    'acquire', 'acquittal', 'acreage', 'across', 'address', 'adolescence', 'adulterate', 'advantageous',
    'advice', 'advisable', 'affect', 'aggressive', 'allegiance', 'alleged', 'allotted', 'amateur',
    'ambiguous', 'amenable', 'amortize', 'anesthetize', 'annihilate', 'anomaly', 'anonymous', 'antarctic',
    'antecedent', 'antenna', 'anxious', 'apparent', 'appearance', 'appropriate', 'arbitrary', 'argument',
    'arithmetic', 'arrhythmia', 'ascend', 'asymmetry', 'athlete', 'attitude', 'auxiliary', 'awkward',
    'bachelor', 'bacteria', 'balsamic', 'barbecue', 'basically', 'beautiful', 'beginning', 'believe',
    'bellwether', 'beneficiary', 'beneficial', 'berserk', 'besieged', 'bizarre', 'blossom', 'bouquet',
    'boundary', 'brahmin', 'braille', 'breath', 'breathe', 'bulletin', 'bureaucracy', 'business',
    'calendar', 'camouflage', 'cantaloupe', 'category', 'cemetery', 'changeable', 'characteristic',
    'chauffeur', 'chauvinism', 'chicanery', 'chili', 'chlorophyll', 'cholesterol', 'chrysanthemum',
    'circumference', 'circumstances', 'colonel', 'colloquial', 'column', 'commemorate', 'committed',
    'committee', 'companion', 'comparative', 'competent', 'concede', 'conceivable', 'conscience',
    'conscientious', 'conscious', 'consensus', 'consistent', 'controversial', 'convenient', 'coolly',
    'corroborate', 'counterfeit', 'coup', 'courteous', 'crystallize', 'curriculum', 'daiquiri',
    'dachshund', 'deceive', 'definitely', 'defibrillator', 'defendant', 'defiant', 'deficit', 'desirable',
    'desperate', 'deterrent', 'develop', 'diaphragm', 'diarrhea', 'dilemma', 'dilettante', 'dimension',
    'diphtheria', 'disappear', 'disappoint', 'disastrous', 'discipline', 'disease', 'dissent', 'dividend',
    'draught', 'drunkenness', 'dumbbell', 'dysentery', 'ecstasy', 'efficiency', 'eighth', 'either',
    'elegant', 'eligible', 'eliminate', 'embarrass', 'embryo', 'eminent', 'encyclopedia', 'enumerable',
    'envy', 'enzyme', 'equipped', 'equivalent', 'erroneous', 'esophagus', 'exaggerate', 'exceed',
    'excellent', 'exercise', 'exhilarate', 'existence', 'experience', 'exuberance', 'facade', 'fascinating',
    'feasible', 'February', 'fiery', 'finally', 'financially', 'fluorescent', 'foreign', 'forfeit',
    'fourth', 'fulfill', 'fundamentally', 'fungible', 'gauge', 'generally', 'generous', 'genius',
    'government', 'governor', 'grammar', 'grandeur', 'grateful', 'guarantee', 'guerrilla', 'guidance',
    'gymnasium', 'handkerchief', 'harass', 'height', 'hemorrhage', 'hieroglyphics', 'hierarchy',
    "hors d'oeuvres", 'humorous', 'hygiene', 'hypocrisy', 'hypocrite', 'hypothetical', 'identical',
    'idiosyncrasy', 'immediately', 'implement', 'incidentally', 'independent', 'indispensable',
    'inoculate', 'intelligence', 'interrupt', 'irascible', 'irresistible', 'isthmus', 'jalapeno',
    'janitor', 'jealous', 'jewelry', 'judgment', 'kernel', 'khaki', 'knowledge', 'laboratory',
    'leisure', 'liaison', 'library', 'license', 'lightning', 'liquefy', 'loneliness', 'maintenance',
    'maneuver', 'marshmallow', 'mathematics', 'medieval', 'memento', 'millennium', 'miniature',
    'minuscule', 'mischievous', 'misspell', 'mortgage', 'mosquito', 'necessary', 'negotiate',
    'neighbor', 'niece', 'noticeable', 'occurred', 'occurrence', 'octopus', 'officially', 'omission',
    'ophthalmologist', 'optimism', 'outrageous', 'parallel', 'parliament', 'pastime', 'pavilion',
    'perseverance', 'personal', 'personnel', 'perspective', 'pharaoh', 'phenomenon', 'physician',
    'piece', 'plagiarism', 'playwright', 'pneumonia', 'possession', 'potatoes', 'precede', 'prejudice',
    'prevalent', 'privilege', 'pronunciation', 'prophecy', 'publicly', 'punctuation', 'quarantine',
    'questionnaire', 'queue', 'quietly', 'quite', 'quizzes', 'raspberry', 'receive', 'recommend',
    'referred', 'reference', 'relevant', 'religious', 'remembrance', 'reservoir', 'restaurant',
    'rhapsody', 'rhythm', 'ridiculous', 'sacrilegious', 'sandwich', 'satellite', 'scenario', 'schedule',
    'scissors', 'secretary', 'separate', 'sergeant', 'siege', 'similar', 'simile', 'skilful', 'souvenir',
    'specifically', 'spectacular', 'spontaneous', 'statistical', 'stubbornness', 'subtle', 'succeed',
    'successful', 'succession', 'sufficient', 'supersede', 'surprise', 'syllable', 'symmetry', 'synonym',
    'technique', 'temperature', 'tendency', 'thorough', 'threshold', 'tomorrow', 'tournament', 'tragedy',
    'treacherous', 'twelfth', 'tyranny', 'unanimous', 'unconscious', 'unfortunately', 'unique', 'vacuum',
    'vegetable', 'vehicle', 'vengeance', 'view', 'villain', 'weather', 'Wednesday', 'weird', 'yacht'
]
