import os
import shutil
import kivy
import assets.word_search as ws

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from kivy.resources import resource_find
from kivy.app import App
from kivy.resources import resource_find
from kivy.lang import Builder


kivy.require('1.9.0')

if platform in ('win', 'linux', 'macosx'):
    # Set window size for desktop
    Window.size = (700, 600)
    Window.resizable = False

class RootWidget(BoxLayout):

    def __init__(self):
        super(RootWidget, self).__init__()
        self.selected_option = 'Medium'
        self.create_dropdown() # User Proficiency Dropdown
        self.suggestion_dropdown = DropDown(auto_dismiss=False) # Create suggestion dropdown


    def on_kv_post(self, base_widget):
        self.word_definitions = ws.load_word_definitions()  # Load word definitions
        self.ids.entry.bind(text=self.update_search_suggestions)  # Bind text change to update suggestions
        self.ids.entry.bind(on_text_validate=self.on_enter_pressed)
        Window.bind(on_key_down=self.handle_key_navigation)
        self.suggestion_buttons = []  # List to store suggestion buttons
        self.highlight_index = 0      # Tracks which suggestion is highlighted

        self.is_black_theme = True  # default to black theme
        self.set_theme(self.is_black_theme)

        


    def create_dropdown(self):
        self.dropdown = DropDown()
        self.dropdown.clear_widgets()

        options = ['Low', 'Medium', 'High']
        for option in options:
            btn = Button(
                text=option,
                size_hint_y=None,
                height=40,
                font_size=22,
                bold=True,
                color=(1, 1, 1, 1),
                background_normal='',
                background_color=(0.1, 0.1, 0.1, 1)  # default bg

            )
            btn.bind(on_release=lambda btn_instance=btn: self.on_select_option(btn_instance))
            self.dropdown.add_widget(btn)

        main_btn = self.ids.proficiency_level
        main_btn.text = self.selected_option  # default value
        main_btn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(main_btn, 'text', x))
        self.update_highlight()  # initial highlight

    def on_select_option(self, btn_instance):
        self.selected_option = btn_instance.text
        self.ids.proficiency_level.text = self.selected_option
        self.dropdown.dismiss()
        self.update_highlight()

    def update_highlight(self):
        for widget in self.dropdown.container.children:
            if isinstance(widget, Button):
                if widget.text == self.selected_option:
                     widget.background_color = (0.5, 0.5, 0.5, 1)  # grey highlight
                else:
                    widget.background_color = (0.1, 0.1, 0.1, 1)  # normal

    
    def set_theme(self, is_black):
        self.is_black_theme = is_black  # Store current theme state (True = Black theme)

        if is_black:
            # --- Black Theme ---
            theme = {
                "bg": (0, 0, 0, 1),                             # Black background
                "text_color": (1, 1, 1, 1),                     # White text
                "container_colour": (0.145, 0.145, 0.145, 1),   # Dark grey container
                "theme_icon": resource_find("assets/Grey/sunglasses_grey.png"),  # Light theme icon
                "trash_icon": resource_find("assets/Grey/trash_grey.png"),
                "question_mark_icon": resource_find("assets/Grey/question_mark_grey.png"),
                "download_icon": resource_find("assets/Grey/download_grey.png")
            }
        else:
            # --- Yellow Theme ---
            theme = {
                "bg": (0.788, 0.643, 0.016, 1),                 # Yellow background
                "text_color": (0, 0, 0, 1),                     # Black text
                "container_colour": (0.125, 0.125, 0.125, 1),   # Black container
                "theme_icon": resource_find("assets/Black/moon_black.png"),      # Dark theme icon
                "trash_icon": resource_find("assets/Black/trash_black.png"),
                "question_mark_icon": resource_find("assets/Black/question_mark_black.png"),
                "download_icon":resource_find("assets/Black/download_black.png")
            }

        # Apply background color to root container
        with self.canvas.before:
            Color(*theme["bg"])
            Rectangle(pos=self.pos, size=self.size)

        # Set theme-related icons
        self.ids.current_theme_icon.source = theme["theme_icon"]
        self.ids.clear_cache_icon.source = theme["trash_icon"]
        self.ids.help_icon.source = theme["question_mark_icon"]
        self.ids.download_icon.source = theme["download_icon"]

        # Apply container color to input/output boxes
        self.ids.entry.background_color = theme["container_colour"]
        self.ids.output_box.background_color = theme["container_colour"]

        # Apply text color
        self.ids.book_label.color = theme["text_color"]
        self.ids.proficiency_label.color = theme["text_color"]
        self.ids.entry.cursor_color = theme["text_color"]


    def toggle_theme(self):
        # Toggle between Black and Yellow themes
        self.set_theme(not self.is_black_theme)


    def get_last_book_name(self):
        return ws.get_last_book_name()

    def search_word(self):
        ws.search_word(self.ids.entry, self.ids.output_box, self.word_definitions)

    def clear_cache(self):
        self.word_definitions = {}
        return ws.clear_cache(self.ids.output_box, self.ids.book_label)
        

    def show_user_manual(self):
        return ws.show_user_manual(self.ids.output_box)

    def upload_callback(self, pdf_path):
        new_word_definitions = ws.upload_and_process_pdf(
            self.ids.proficiency_level.text,
            pdf_path,
            self.ids.output_box,
            self.ids.book_label
        )
        if new_word_definitions: 
            self.word_definitions = new_word_definitions

    def select_pdf(self):
        return ws.open_filechooser(self.upload_callback) 
        # passing a callback function — self.upload_callback to be called later with the pdf path which
        # then call the function to process that process the pdf


    def handle_key_navigation(self, window, key, scancode, codepoint, modifiers):
        if not self.suggestion_buttons:
            return

        if key == 273:  # Up arrow
            self.highlight_index = (self.highlight_index - 1) % len(self.suggestion_buttons)
            self.highlight_suggestion(self.highlight_index)
        elif key == 274:  # Down arrow
            self.highlight_index = (self.highlight_index + 1) % len(self.suggestion_buttons)
            self.highlight_suggestion(self.highlight_index)
        elif key == 13:  # Enter key
            selected_word = self.suggestion_buttons[self.highlight_index].text
            self.apply_selected_suggestion(selected_word)


    def highlight_suggestion(self, index):
        for i, btn in enumerate(self.suggestion_buttons):
            if i == index:
                btn.background_color = (0.2, 0.4, 1, 1)  # Blue
            else:
                btn.background_color = (0, 0, 0, 1)

    def on_enter_pressed(self, instance):
        if self.suggestion_buttons:
            selected_word = self.suggestion_buttons[self.highlight_index].text
            self.apply_selected_suggestion(selected_word)


    def apply_selected_suggestion(self, word):
        self.ids.entry.text = word
        self.suggestion_dropdown.dismiss()
        self.search_word()

    
    def update_search_suggestions(self, instance, text):
        self.suggestion_dropdown.dismiss()
        self.suggestion_dropdown = DropDown(auto_dismiss=False)
        self.suggestion_buttons = []
        self.highlight_index = 0

        typed_word = text.strip().lower()
        if not typed_word:
            return

        matches = [w for w in self.word_definitions if w.startswith(typed_word)]
        for word in matches[:10]:
            btn = Button(
                text=word,
                size_hint_y=None,
                height=40,
                halign='left',
                background_normal='',
                background_color=(0, 0, 0, 1),
                color=(1, 1, 1, 1),
                padding=(10, 10),
                bold=True
            )
            btn.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
            btn.bind(on_release=lambda btn: self.apply_selected_suggestion(btn.text))
            self.suggestion_dropdown.add_widget(btn)
            self.suggestion_buttons.append(btn)

        if matches:
            self.highlight_suggestion(0)
            self.suggestion_dropdown.open(self.ids.entry) # Anchor to entry
            self.suggestion_dropdown.width = self.ids.entry.width

    def copy_common_words_if_missing(self):
        app_dir = App.get_running_app().user_data_dir
        os.makedirs(app_dir, exist_ok=True)

        dst_path = os.path.join(app_dir, "common_words.txt")
        if not os.path.exists(dst_path):
            src_path = resource_find("Common Words/combined_common_words.txt")
            if src_path:
                shutil.copy(src_path, dst_path)
                print(f"Copied common_words.txt to {dst_path}")
            else:
                print("Source common_words.txt not found in assets!")

    def download_file(self):
        return ws.download_file(self.ids.output_box,self.ids.book_label)


class WordSearchApp(App):

    def build(self):
        Builder.load_file('wordsearchapp.kv')  # or load_string if using string
        self.root_widget = RootWidget()  # save root widget instance
        return self.root_widget
    
    def on_start(self):
        self.root_widget.copy_common_words_if_missing()  # now this works
        if self.root.ids.book_label.text == "No book loaded":
            self.root.ids.output_box.text = (
                "> Please upload a book file to begin.\n"
                "> For more information, click the question mark icon on the top-right corner."
            )


if __name__ == '__main__':
    WordSearchApp().run()




