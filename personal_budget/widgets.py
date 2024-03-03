from textual.widgets import RadioButton
from textual.widgets import RadioSet
from textual.message import Message
from textual.widget import Widget


class Radio(Widget):
    class ValueChanged(Message):
        """The value of the radio set has changed."""

        def __init__(self, value):
            self.value = value
            super().__init__()

    def __init__(
        self,
        options: dict[str, str],
        selected_index: int | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.options = options
        self.selected_index = selected_index
        self.value = None
        if selected_index is not None:
            self.value = list(self.options.keys())[selected_index]

    def compose(self):
        with RadioSet():
            for index, (_, label) in enumerate(self.options.items()):
                yield RadioButton(label, value=index == self.selected_index)

    def on_radio_set_changed(self, event: RadioSet.Changed):
        self.value = list(self.options.keys())[event.radio_set.pressed_index]
        self.post_message(self.ValueChanged(self.value))
