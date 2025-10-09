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
            ok = not self.chat_interface.session.app.current_buffer.complete_state
            ok = ok and self.chat_interface.session.app.current_buffer.document.is_cursor_at_the_end
            return ok

        @Condition
        def not_eob():
            return not self.chat_interface.session.app.current_buffer.document.is_cursor_at_the_end

        @Condition
        def is_not_completing():
            return not self.chat_interface.session.app.current_buffer.complete_state

        @Condition
        def is_completing():
            return self.chat_interface.session.app.current_buffer.complete_state

        @Condition
        def is_empty_buffer():
            buffer = self.chat_interface.session.app.current_buffer
            return buffer.text == '' and buffer.cursor_position == 0

        @Condition
        def starts_with_slash():
            """Check if buffer text starts with a slash"""
            buffer = self.chat_interface.session.app.current_buffer
            return buffer.text.strip().startswith('/')

        # @bindings.add('up', filter=is_not_completing)
        # def custom_up(event):
        #     # Your custom behavior for up key
        #     # print("Custom up key pressed")
        #     pass

        # @bindings.add('down', filter=is_not_completing)
        # def custom_down(event):
        #     # Your custom behavior for down key
        #     # print("Custom down key pressed")
        #     pass

        # @bindings.add('escape', eager=True, filter=is_completing)
        # def _(event):
        #     """Use Esc key to cancel completion"""
        #     buffer = event.app.current_buffer
        #     buffer.cancel_completion()

        @bindings.add('tab', filter=is_completing)
        def _(event):
            """Select the current completion or move to the next one."""
            buffer = event.current_buffer
            completion = buffer.complete_state.current_completion
            if completion:
                buffer.apply_completion(completion)
                # buffer.insert_text(" ")
            else:
                buffer.complete_next()
            buffer.complete_state = None

        # @bindings.add('enter', eager=True, filter=is_completing)
        # def _(event):
        #     """Select the current completion or move to the next one."""
        #     buffer = event.current_buffer
        #     completion = buffer.complete_state.current_completion
        #     if completion:
        #         buffer.apply_completion(completion)
        #         # buffer.insert_text(" ")
        #     else:
        #         buffer.complete_next()
        #     buffer.complete_state = None

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

        # @bindings.add('enter')
        # def _(event):
        #     buffer = event.app.current_buffer
        #     if buffer.document.is_cursor_at_the_end or True:
        #         buffer.validate_and_handle()
        #     else:
        #         buffer.insert_text('\n')

        # @bindings.add('escape', 'enter', eager=True)
        # def _(event):
        #     buffer = event.app.current_buffer
        #     buffer.insert_text('\n')

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

        @bindings.add('escape', 'N')
        def _(event):
            """Option+Shift+N: Reset chat history (same as /r)"""
            buffer = event.app.current_buffer
            buffer.text = '/r'
            buffer.validate_and_handle()

        @bindings.add('enter', filter=starts_with_slash)
        def _(event):
            """Submit command when Enter is pressed and input starts with slash"""
            buffer = event.current_buffer
            buffer.validate_and_handle()

        return bindings
