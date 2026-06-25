from django.conf import settings
from django.db import models
from django.utils import timezone


class Trade(models.Model):
    DIRECTION_CHOICES = [("Compra", "Compra"), ("Venda", "Venda")]
    RESULT_CHOICES = [("Gain", "Gain"), ("Loss", "Loss"), ("Zero", "Zero")]
    EXECUTION_CHOICES = [("A+", "A+"), ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="criado em")
    trade_date = models.DateField(default=timezone.localdate, verbose_name="data do trade")
    entry_time = models.TimeField(blank=True, null=True, verbose_name="hora de entrada")
    exit_time = models.TimeField(blank=True, null=True, verbose_name="hora de saída")
    symbol = models.CharField(max_length=120, verbose_name="ativo")
    market = models.CharField(max_length=120, blank=True, verbose_name="mercado")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="direção")
    setup = models.CharField(max_length=120, blank=True, verbose_name="setup")
    timeframe = models.CharField(max_length=40, blank=True, default="1M", verbose_name="timeframe")
    account = models.CharField(max_length=120, blank=True, verbose_name="conta")
    entry_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="preço de entrada")
    exit_price = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, verbose_name="preço de saída")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=1, verbose_name="quantidade")
    stop_loss = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, verbose_name="stop loss")
    target_price = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, verbose_name="alvo")
    fees = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="taxas")
    planned_trade = models.BooleanField(default=True, verbose_name="operação planejada")
    market_context = models.TextField(blank=True, verbose_name="contexto de mercado")
    entry_reason = models.TextField(blank=True, verbose_name="motivo da entrada")
    exit_reason = models.TextField(blank=True, verbose_name="motivo da saída")
    emotion_before = models.CharField(max_length=120, blank=True, verbose_name="emoção antes")
    emotion_during = models.CharField(max_length=120, blank=True, verbose_name="emoção durante")
    emotion_after = models.CharField(max_length=120, blank=True, verbose_name="emoção depois")
    execution_grade = models.CharField(max_length=5, blank=True, choices=EXECUTION_CHOICES, verbose_name="nota de execução")
    mistakes = models.TextField(blank=True, verbose_name="erros")
    lessons = models.TextField(blank=True, verbose_name="lições")
    followed_plan = models.BooleanField(default=True, verbose_name="seguiu o plano")
    screenshot = models.ImageField(upload_to="screenshots/", blank=True, null=True, verbose_name="print")
    result = models.CharField(max_length=10, blank=True, choices=RESULT_CHOICES, verbose_name="resultado")
    pnl = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="pnl")
    initial_risk = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="risco inicial")
    r_multiple = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="múltiplo de r")
    risk_reward = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="risco/retorno")
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="duração em minutos")

    def __str__(self):
        return f"{self.trade_date} - {self.symbol}"

    class Meta:
        verbose_name = "trade"
        verbose_name_plural = "trades"


class JournalOption(models.Model):
    KIND_CHOICES = [("setup", "Setup"), ("emotion", "Emotion")]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, verbose_name="tipo")
    label = models.CharField(max_length=120, unique=True, verbose_name="nome")

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = "opção do diário"
        verbose_name_plural = "opções do diário"
