import os
import re
import time
import threading

class WordListManager:
    """Manages a list of unique words"""
    def __init__(self, word_list: list[str], save_file: str = None, auto_save: bool = True):
        self.word_list = word_list

        if save_file is not None:
            self.save_file = os.path.expanduser(save_file)
            self.add_words(self.load_from_file())

        self.auto_save = auto_save
        self.save_interval = 30  # 30 seconds in seconds
        self.stop_event = threading.Event()

        if auto_save:
            self.schedule_save()

    # def __del__(self):
    #     self.stop()
    #     self.save_to_file()

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
        print("Auto-save stopped.")

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

        # aquire a lock on the file
        lock_file_name = self.save_file + '.lock'
        start_time = time.time()
        max_wait_time = 2
        while os.path.exists(lock_file_name):
            time.sleep(0.1)
            if time.time() - start_time > max_wait_time:
                print(f"Timeout waiting for lock file {lock_file_name}, going ahead anyway")
                break

        lock_file = open(self.save_file + '.lock', 'w')
        lock_file.close()

        if not os.path.exists(self.save_file):
            # touch the file if it doesn't exist
            with open(self.save_file, 'w') as file:
                file.write('')
        existing_words = self.load_from_file()
        self.word_list = list(set(self.word_list + existing_words))

        with open(self.save_file, 'w') as file:
            file.write('\n'.join(self.word_list))

        # remove the lock file
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
