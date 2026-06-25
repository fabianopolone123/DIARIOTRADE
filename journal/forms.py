from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import JournalOption, Trade

NEW_OPTION = "+ Cadastrar novo"


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}))


class TradeForm(forms.ModelForm):
    setup = forms.ChoiceField(choices=(), required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_before = forms.ChoiceField(choices=(), required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_during = forms.ChoiceField(choices=(), required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_after = forms.ChoiceField(choices=(), required=False, widget=forms.Select(attrs={"class": "input"}))

    def __init__(self, *args, **kwargs):
        setup_choices = kwargs.pop("setup_choices", None)
        emotion_choices = kwargs.pop("emotion_choices", None)
        super().__init__(*args, **kwargs)
        if setup_choices is None:
            setup_choices = list(
                JournalOption.objects.filter(kind="setup").order_by("label").values_list("label", "label")
            )
        if emotion_choices is None:
            emotion_choices = list(
                JournalOption.objects.filter(kind="emotion").order_by("label").values_list("label", "label")
            )
        self.fields["setup"].choices = [("", "--------")] + setup_choices + [(NEW_OPTION, NEW_OPTION)]
        self.fields["setup"].widget.attrs["data-new-option"] = NEW_OPTION
        emotion_choices_with_new = [("", "--------")] + emotion_choices + [(NEW_OPTION, NEW_OPTION)]
        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            self.fields[key].choices = emotion_choices_with_new
            self.fields[key].widget.attrs["data-new-option"] = NEW_OPTION
        if self.instance and self.instance.pk and self.instance.setup and self.instance.setup not in dict(self.fields["setup"].choices):
            self.fields["setup"].choices = [("", "--------"), (self.instance.setup, self.instance.setup)] + setup_choices + [(NEW_OPTION, NEW_OPTION)]
        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            value = getattr(self.instance, key, "")
            if self.instance and self.instance.pk and value and value not in dict(self.fields[key].choices):
                self.fields[key].choices = [("", "--------"), (value, value)] + emotion_choices + [(NEW_OPTION, NEW_OPTION)]

    class Meta:
        model = Trade
        fields = [
            "trade_date",
            "entry_time",
            "exit_time",
            "symbol",
            "direction",
            "setup",
            "timeframe",
            "entry_price",
            "exit_price",
            "quantity",
            "stop_loss",
            "target_price",
            "planned_trade",
            "followed_plan",
            "market_context",
            "entry_reason",
            "exit_reason",
            "emotion_before",
            "emotion_during",
            "emotion_after",
            "execution_grade",
            "mistakes",
            "lessons",
            "result",
            "screenshot",
        ]
        widgets = {
            "trade_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "entry_time": forms.TimeInput(attrs={"type": "time", "class": "input"}),
            "exit_time": forms.TimeInput(attrs={"type": "time", "class": "input"}),
            "symbol": forms.TextInput(attrs={"class": "input", "placeholder": "Mini Índice"}),
            "direction": forms.Select(attrs={"class": "input"}),
            "timeframe": forms.TextInput(attrs={"class": "input"}),
            "entry_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "exit_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "stop_loss": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "target_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "planned_trade": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "followed_plan": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "market_context": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "Último contexto será reaproveitado automaticamente"}),
            "entry_reason": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "exit_reason": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "execution_grade": forms.Select(attrs={"class": "input"}),
            "mistakes": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "lessons": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "result": forms.Select(attrs={"class": "input"}),
            "screenshot": forms.ClearableFileInput(attrs={"class": "input"}),
        }
