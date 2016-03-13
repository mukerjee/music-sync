from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.clock import Clock

from functools import partial

output_mesg_queue = []

Builder.load_string('''
<ScrollableLabel>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')


class ScrollableLabel(ScrollView):
    text = StringProperty('')


class SyncWindow(GridLayout):
    def __init__(self, **kwargs):
        global chat_box
        super(SyncWindow, self).__init__(**kwargs)

        self.cols = 1

        chat_box = ScrollableLabel(text='Welcome')
        self.add_widget(chat_box)

        textinput = TextInput(text='', multiline=False)
        textinput.bind(on_text_validate=self.on_enter)
        self.add_widget(textinput)

    def on_enter(self, text_box):
        if text_box.text:
            output_mesg_queue.append(text_box.text)
        text_box.text = ""
        Clock.schedule_once(partial(self.refocus, text_box))

    def refocus(self, text_box, *largs):
        text_box.focus = True


class MyApp(App):
    def build(self):
        return SyncWindow()


def run():
    MyApp().run()
