import fitz 
import re

import difflib
import os
import sys

from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
from nltk.corpus import wordnet 
from wordfreq import word_frequency
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from textwrap import wrap
from kivy.resources import resource_find



from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock


def extract_pdf_pages(file_path):
    """
    Extracts text page-by-page from a PDF file.

    Args:
        file_path (str): Path to the PDF.

    Returns:
        list: A list of strings, one per PDF page.
    """
    try:
        doc = fitz.open(file_path)
        pages = [page.get_text() for page in doc]
        doc.close()
        return pages
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return []

def clean_text(text):
    """
    Cleans the text by removing punctuation and converting to lowercase.
    This helps with word matching.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    if text.isdigit() or len(text)<2:
        return None  # Skip pure numbers
        
    text = re.sub(r"'s$", '', text)  # Remove trailing possessive
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'[^A-Za-z]', '', text)  # Remove non-alphabetic characters

    cleaned = text.lower()
    return cleaned if cleaned else None

def get_word_definition(word, definition_cache):
    """
    Caching and retrieving word definitions from WordNet.
    """
    if word in definition_cache:
        return definition_cache[word]
    
    synsets = wordnet.synsets(word)
    if synsets:
        definition = synsets[0].definition()
        definition_cache[word] = definition
        return definition
    else:
        definition_cache[word] = None
        return None

def append_to_common_words_batch(words, file_path):
    """
    Appends a batch of words to the common words file.

    Args:
        words (list): List of words to append.
        file_path (str): Path to the file where words will be appended.
    """

    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            # Write all words at once to avoid repeated I/O operations
            file.writelines(f"{word}\n" for word in words)
    except Exception as e:
        print(f"Error writing to file: {e}")


def get_difficult_word_frequencies(pages, common_words):
    """
    Given the extracted pages, counts the frequency of difficult words not in the common_words list.
    """
    word_frequency = Counter()
    cleaned_words = set()
    
    for page in pages:
        words = word_tokenize(page) 
        for raw_word in words:
            cleaned_word = clean_text(raw_word)  # Clean each word individually
            if cleaned_word and cleaned_word not in common_words:
                    word_frequency[cleaned_word] += 1
                    cleaned_words.add(cleaned_word)
                
    return word_frequency,cleaned_words


def identify_difficult_words(cleaned_words,word_frequency_dict, local_limit, 
                             global_freq_limit, common_word_lower_limit,common_words_file_path):

    """
    Identifies difficult words using both local and global frequency.
    Appends globally common words to a combined common words file.

    Returns:
        dict: {word: definition}
    """


    difficult_words = {}
    definition_cache = {}
    new_common_words = []
    

    for cleaned_word in cleaned_words:  # Iterate over pre-cleaned words
        local_freq = word_frequency_dict.get(cleaned_word, 0)
        
        if local_freq <= local_limit:
            # Passed local check → accept
            definition = get_word_definition(cleaned_word, definition_cache)
            if definition:
                difficult_words[cleaned_word] = definition
        else:
            # Failed local → check global rank
            global_freq = word_frequency(cleaned_word, 'en', wordlist='large', minimum=0.0)
            if global_freq < global_freq_limit:
                # Word is globally rare → accept
                definition = get_word_definition(cleaned_word, definition_cache)
                if definition:
                    difficult_words[cleaned_word] = definition
            elif common_word_lower_limit < local_freq:
                # Word is rejected by wordfreq (i.e., it is common globally)
                new_common_words.append(cleaned_word)

    # After processing all words, append all common words to the common words file at once
    if new_common_words:
        append_to_common_words_batch(new_common_words,common_words_file_path)

    return difficult_words, len(new_common_words)


def load_common_words(filepath):
    """Loads common words from a file into a set.

       Args:
          filepath (str): Path to the common words file.

       Returns:
          set: A set of common words.
    """
    common_words = set()
    try:
        with open(filepath, 'r') as f:
            for line in f:
                common_words.add(line.strip())
    except FileNotFoundError:
        print(f"Common words file not found at {filepath}. Using a small default list.")
        #  A very small default list if the file isn't found. For testing.
        common_words = {"the", "and", "is", "of", "a", "an", "in", "to", "it", 
                        "that", "was", "he", "she", "for", "on", "are", "with", "as", "I",
                          "his", "they", "at", "be", "this", "have", "from", "or", "had", "but", "not"}
    except Exception as e:
        print(f"Error reading common words file: {e}")
        common_words = {"the", "and", "is", "of", "a", "an", "in", "to", "it", "that",
                         "was", "he", "she", "for", "on", "are", "with", "as", "I", "his",
                           "they", "at", "be", "this", "have", "from", "or", "had", "but", "not"}  # even smaller list
    return common_words


def search_word(entry, output_box, word_definitions):
    word = entry.text.strip().lower()
    # output_box.text = ""  # Clear previous output

    definition = word_definitions.get(word)
    if definition:
        output_box.text = f"{word}: {definition}"
    else:
        suggestions = difflib.get_close_matches(word, word_definitions.keys(), n=3)
        if suggestions:
            output_box.text = "Word not found. Did you mean:\n" + "\n".join(
                f"- {s}: {word_definitions[s]}" for s in suggestions
            )
        else:
            output_box.text = "Word not found."


def get_last_book_name(definitions_file="difficult_words_definitions.txt"):
    app_dir = App.get_running_app().user_data_dir
    full_path = os.path.join(app_dir, definitions_file)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__book_name__:"):
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        return "No book loaded"
    return "No book loaded"


# Function to load word definitions from the file
def load_word_definitions(file_path="difficult_words_definitions.txt"):
    word_definitions = {}
    app_dir = App.get_running_app().user_data_dir
    full_path = os.path.join(app_dir, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():  # Ignore empty lines
                    word, definition = line.split(':', 1)  # Split word and definition
                    word_definitions[word.strip().lower()] = definition.strip()  # Store in dictionary
    except FileNotFoundError:
        print(f"File not found at {file_path}. Please check the path.")
    return word_definitions


def open_filechooser(upload_callback):
    content = FileChooserListView(filters=["*.pdf"])
    popup = Popup(title="Select PDF file", content=content, size_hint=(0.9, 0.9))

    def on_file_select(instance, selection, touch):
        if selection:
            popup.dismiss()
            pdf_path = selection[0]
            Clock.schedule_once(lambda dt: upload_callback(pdf_path))

    content.bind(on_submit=on_file_select)
    popup.open()


def upload_and_process_pdf(proficiency_level,pdf_path, output_box, book_label):
    
    proficiency_settings = {
        "Low": {"local_limit": 70, "global_freq_limit": 1e-5, "common_word_lower_limit": 100},
        "Medium": {"local_limit": 45, "global_freq_limit": 1e-6, "common_word_lower_limit": 75},
        "High": {"local_limit": 30, "global_freq_limit": 1e-7, "common_word_lower_limit": 40}
    }

    app_dir = App.get_running_app().user_data_dir
    common_words_file_path = os.path.join(app_dir, "common_words.txt")
    try:
        pages = extract_pdf_pages(pdf_path)
        common_words = load_common_words(common_words_file_path)
        word_freq, cleaned_words = get_difficult_word_frequencies(pages, common_words)

        level = proficiency_level  
        settings = proficiency_settings.get(level, proficiency_settings["Medium"])

        difficult_words, new_common_words_len = identify_difficult_words(
            cleaned_words=cleaned_words,
            word_frequency_dict=word_freq,
            local_limit=settings["local_limit"],
            global_freq_limit=settings["global_freq_limit"],
            common_word_lower_limit=settings["common_word_lower_limit"],
            common_words_file_path=common_words_file_path
        )

        book_name = os.path.splitext(os.path.basename(pdf_path))[0]

        output_lines = []
        if new_common_words_len > 0:
            output_lines.append(f"Appended {new_common_words_len} words to common words.")
        output_lines.append(f"{book_name} analyzed successfully.")
        output_lines.append(f"{len(difficult_words)} difficult words updated.")
        output_text = "\n".join(output_lines)

        app_dir = App.get_running_app().user_data_dir
        definitions_path = os.path.join(app_dir, "difficult_words_definitions.txt")

        with open(definitions_path, "w", encoding="utf-8") as def_file:
            if book_name:
                def_file.write(f"__book_name__: {book_name}\n")
            for word, definition in difficult_words.items():
                def_file.write(f"{word}: {definition}\n")

        word_definitions = load_word_definitions()

        book_label.text = book_name
        output_box.text = output_text

        return word_definitions

    except Exception as e:
        book_label.text = "Failed to load book"
        output_box.text = f"Error processing PDF:\n{e}"
        

def show_user_manual(output_box):
    help_text = (
        f"{' ' * 60} How to Use the App:\n"
        "1. Click ‘Upload PDF and Extract’ to load and analyze any PDF book or document.\n"
        "2. Before uploading, choose your Proficiency Level on the left:\n"
        "   - Low: Highlights most uncommon words.\n"
        "   - Medium: Balanced filtering.\n"
        "   - High: Only very rare words shown.\n"
        "3. The app will extract text, identify difficult words using frequency data, and save them.\n"
        "4. You can search for meanings of words using the search bar at the top.\n"
        "5. Click trash button on top left corner to clear previously analyzed data \n"
        "6. Click on theme button to toggle between themes to reduce eye strain.\n"
        "7. Your common word list grows smarter based on your interactions.\n"
        "8. Internet is only required during PDF upload for fetching word meanings.Once processed, everything works offline for distraction-free reading.\n"
        "9. For best results, use clean, text-based PDFs (not scanned images or pictures).\n"
        "10. Each new upload replaces previous analysis—only one book is active at a time.\n"
        "11. The app is built for Windows, not Android. However, it provides a downloadable, lightweight PDF containing all definitions, which you can open on any Android device and easily search for words within."

        f"\n\n{' ' * 15}Tip: Use this app for focused, offline reading without digital distractions."
    )
    output_box.text = help_text


def clear_cache(output_box,book_label):
    def confirm_action(instance):
        try: # a line continuation character \
            app_dir = App.get_running_app().user_data_dir

            # Source file inside your packaged assets
            src_path = resource_find("assets/combined_common_words.txt")

            # Destination files inside your writable app directory
            dst_path = os.path.join(app_dir, "common_words.txt")
            definitions_path = os.path.join(app_dir, "difficult_words_definitions.txt")

            if book_label.text == "No book loaded":
                output_box.text = "No book loaded.\nNothing to clear."
            elif os.path.exists(definitions_path) and os.path.getsize(definitions_path) == 0:
                output_box.text = "Definitions file is already empty."
            else:
                with open(src_path, "r", encoding="utf-8") as src, \
                    open(dst_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())

                # Clear definitions file
                open(definitions_path, "w", encoding="utf-8").close()
                output_box.text = "Cache cleared.\ncommon_words.txt reset.\nDefinitions emptied."
                book_label.text = "No book loaded"
        except Exception as e:
            output_box.text = f"Failed to clear cache:\n{e}"
        popup.dismiss()

    def cancel_action(instance):
        output_box.text = "Cache clear action cancelled."
        popup.dismiss()

     # UI layout
    content = BoxLayout(orientation='vertical', spacing=15, padding=15)
    content.add_widget(Label(
        text="[b]Are you sure you want to clear the cache?[/b]",
        markup=True,
        halign="center"
    ))

    btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
    btn_yes = Button(
        text="Yes", 
        background_color=(0.2, 0.6, 0.2, 1),
        size_hint=(0.2, 1.5),
        font_size=20
    )
    btn_no = Button(
        text="No", 
        background_color=(0.6, 0.2, 0.2, 1),
        size_hint=(0.2, 1.5),
        font_size=20
    )
    btn_yes.bind(on_release=confirm_action)
    btn_no.bind(on_release=cancel_action)
    btn_layout.add_widget(btn_yes)
    btn_layout.add_widget(btn_no)

    content.add_widget(btn_layout)

    global popup
    popup = Popup(
        title="Confirm Cache Clear",
        content=content,
        size_hint=(None, None),
        size=(500, 250),
        auto_dismiss=False
    )
    popup.open()


def txt_to_pdf(txt_path, pdf_path):
    with open(txt_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    if not any(line.strip() for line in lines):
        raise ValueError("Text file is empty. PDF will not be created.")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    line_height = 14  # minimal line spacing

    max_chars = 100  # adjust based on font and page width

    for line in lines:
        wrapped_lines = wrap(line.strip(), width=max_chars)
        for wline in wrapped_lines:
            if y < margin:
                c.showPage()
                y = height - margin
            c.drawString(margin, y, wline)
            y -= line_height

    c.save()


def get_download_path(filename):
    if sys.platform == "android":
        from android.storage import primary_external_storage_path
        download_dir = os.path.join(primary_external_storage_path(), "Download")
    else:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    return os.path.join(download_dir, filename)


def download_file(output_box, book_label):
    app_dir = App.get_running_app().user_data_dir
    txt_path = os.path.join(app_dir, "difficult_words_definitions.txt")

    # Sanitize and format the PDF filename using book_label
    safe_label = "".join(c if c.isalnum() or c in (' ', '_', '-') else "_" for c in book_label.text).strip().replace(" ", "_")
    filename = f"{safe_label}_difficult_words_definitions.pdf"
    pdf_path = get_download_path(filename)
    try:
        txt_to_pdf(txt_path, pdf_path)
        output_box.text = f"PDF saved at {pdf_path}"
    except ValueError as e:
        output_box.text = str(e)
    except Exception as e:
        output_box.text(f"An unexpected error occurred: {e}")
    

