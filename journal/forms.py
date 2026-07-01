from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import JournalOption, Trade

NEW_OPTION = "+ Cadastrar novo"


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}))


class TradeForm(forms.ModelForm):
    setup = forms.CharField(required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_before = forms.CharField(required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_during = forms.CharField(required=False, widget=forms.Select(attrs={"class": "input"}))
    emotion_after = forms.CharField(required=False, widget=forms.Select(attrs={"class": "input"}))

    def __init__(self, *args, **kwargs):
        setup_choices = kwargs.pop("setup_choices", None)
        emotion_choices = kwargs.pop("emotion_choices", None)
        super().__init__(*args, **kwargs)

        self.fields["setup"].label = "Setup"
        self.fields["emotion_before"].label = "Emoção antes"
        self.fields["emotion_during"].label = "Emoção durante"
        self.fields["emotion_after"].label = "Emoção depois"
        self.fields["market_context"].label = "Contexto do mercado"
        self.fields["entry_reason"].label = "Motivo da entrada"
        self.fields["exit_reason"].label = "Motivo da saída"
        self.fields["planned_trade"].label = "Operação planejada"
        self.fields["followed_plan"].label = "Seguiu o plano"
        self.fields["result"].label = "Resultado"
        self.fields["screenshot"].label = "Print da tela"
        self.fields["stop_points_net"].label = "Stop líquido (pontos)"
        self.fields["target_points_net"].label = "Pontos líquidos (alvo)"
        self.fields["point_value"].label = "Valor por ponto (R$)"

        if setup_choices is None:
            setup_choices = list(
                JournalOption.objects.filter(kind="setup").order_by("label").values_list("label", "label")
            )
        if emotion_choices is None:
            emotion_choices = list(
                JournalOption.objects.filter(kind="emotion").order_by("label").values_list("label", "label")
            )

        self.fields["setup"].widget.choices = [("", "--------")] + setup_choices + [(NEW_OPTION, NEW_OPTION)]
        self.fields["setup"].widget.attrs["data-new-option"] = NEW_OPTION

        emotion_choices_with_new = [("", "--------")] + emotion_choices + [(NEW_OPTION, NEW_OPTION)]
        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            self.fields[key].widget.choices = emotion_choices_with_new
            self.fields[key].widget.attrs["data-new-option"] = NEW_OPTION

        if self.instance and self.instance.pk and self.instance.setup and self.instance.setup not in dict(self.fields["setup"].widget.choices):
            self.fields["setup"].widget.choices = [("", "--------"), (self.instance.setup, self.instance.setup)] + setup_choices + [(NEW_OPTION, NEW_OPTION)]

        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            value = getattr(self.instance, key, "")
            if self.instance and self.instance.pk and value and value not in dict(self.fields[key].widget.choices):
                self.fields[key].widget.choices = [("", "--------"), (value, value)] + emotion_choices + [(NEW_OPTION, NEW_OPTION)]

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
            "quantity",
            "point_value",
            "stop_loss",
            "stop_points_net",
            "target_price",
            "target_points_net",
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
            "trade_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "input"}),
            "entry_time": forms.TimeInput(format="%H:%M", attrs={"type": "time", "class": "input"}),
            "exit_time": forms.TimeInput(format="%H:%M", attrs={"type": "time", "class": "input"}),
            "symbol": forms.TextInput(attrs={"class": "input", "placeholder": "Mini índice"}),
            "direction": forms.Select(attrs={"class": "input"}),
            "timeframe": forms.TextInput(attrs={"class": "input"}),
            "quantity": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "point_value": forms.NumberInput(attrs={"class": "input", "step": "0.0001"}),
            "stop_loss": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "stop_points_net": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "target_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "target_points_net": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "planned_trade": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "followed_plan": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "market_context": forms.Textarea(attrs={
                "class": "textarea",
                "rows": 4,
                "placeholder": "Ultimo contexto sera reaproveitado automaticamente",
            }),
            "entry_reason": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "exit_reason": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "execution_grade": forms.Select(attrs={"class": "input"}),
            "mistakes": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "lessons": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "result": forms.Select(attrs={"class": "input"}),
            "screenshot": forms.ClearableFileInput(attrs={"class": "input"}),
        }
