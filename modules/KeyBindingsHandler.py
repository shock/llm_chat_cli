from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
import pyperclip

class KeyBindingsHandler:
    def __init__(self, chat_interface):
        self.chat_interface = chat_interface

    def create_key_bindings(self):
        bindings = KeyBindings()

        @Condition
        def is_eob():
            return self.chat_interface.session.app.current_buffer.document.is_cursor_at_the_end

        @Condition
        def not_eob():
            return not self.chat_interface.session.app.current_buffer.document.is_cursor_at_the_end

        @bindings.add('up', filter=is_eob)
        def _(event):
            buffer = event.app.current_buffer
            buffer.history_backward()
            buffer.cursor_position = len(buffer.text)

        @bindings.add('down', filter=is_eob)
        def _(event):
            buffer = event.app.current_buffer
            buffer.history_forward()
            buffer.cursor_position = len(buffer.text)

        @bindings.add('s-up')
        def _(event):
            user_message = self.chat_interface.history.seek_previous_user_message()
            if user_message:
                event.app.current_buffer.text = user_message['content']
            else:
                event.app.current_buffer.text = ''

        @bindings.add('s-down')
        def _(event):
            user_message = self.chat_interface.history.seek_next_user_message()
            if user_message:
                event.app.current_buffer.text = user_message['content']
            else:
                event.app.current_buffer.text = ''

        @bindings.add('enter')
        def _(event):
            buffer = event.app.current_buffer
            if buffer.document.is_cursor_at_the_end or True:
                buffer.validate_and_handle()
            else:
                buffer.insert_text('\n')

        @bindings.add('escape', 'enter')
        def _(event):
            buffer = event.app.current_buffer
            buffer.insert_text('\n')

        @bindings.add('c-b')
        def _(event):
            buffer = event.app.current_buffer
            data = buffer.text
            pyperclip.copy(data)

        @bindings.add('c-l')
        def _(event):
            self.chat_interface.copy_last_response()

        @bindings.add("c-s-down")
        def _(event):
            message = self.chat_interface.history.seek_previous_assistant_message()
            if message:
                self.chat_interface.print_assistant_message(message['content'])
                event.app.exit()

        @bindings.add("c-s-up")
        def _(event):
            if self.chat_interface.history.in_seek_assistant():
                message = self.chat_interface.history.seek_next_assistant_message()
                if message:
                    self.chat_interface.print_assistant_message(message['content'])
                else:
                    self.chat_interface.print_history()
                event.app.exit()

        return bindings
