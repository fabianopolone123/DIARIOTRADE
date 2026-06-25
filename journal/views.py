from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import NEW_OPTION, TradeForm
from .models import JournalOption, Trade


def _compute_metrics(trade):
    entry = trade.entry_price or Decimal("0")
    exit_price = trade.exit_price if trade.exit_price is not None else entry
    qty = trade.quantity or Decimal("0")
    stop_points = abs(trade.stop_loss or Decimal("0"))
    target_points = abs(trade.target_price or Decimal("0"))
    fees = trade.fees or Decimal("0")
    side = Decimal("1") if trade.direction == "Compra" else Decimal("-1")

    pnl = ((exit_price - entry) * qty * side) - fees
    initial_risk = stop_points * qty
    planned_reward = target_points * qty
    trade.pnl = pnl
    trade.initial_risk = initial_risk
    trade.r_multiple = (pnl / initial_risk) if initial_risk else Decimal("0")
    trade.risk_reward = (planned_reward / initial_risk) if initial_risk else Decimal("0")
    if trade.entry_time and trade.exit_time:
        trade.duration_minutes = abs(
            int(
                (
                    (trade.exit_time.hour * 60 + trade.exit_time.minute)
                    - (trade.entry_time.hour * 60 + trade.entry_time.minute)
                )
            )
        )
    return trade


def _setup_choices():
    return list(JournalOption.objects.filter(kind="setup").order_by("label").values_list("label", "label"))


def _emotion_choices():
    return list(JournalOption.objects.filter(kind="emotion").order_by("label").values_list("label", "label"))


class DashboardView(LoginRequiredMixin, ListView):
    model = Trade
    template_name = "journal/dashboard.html"
    context_object_name = "trades"

    def get_queryset(self):
        qs = Trade.objects.all().order_by("-trade_date", "-entry_time", "-id")
        symbol = self.request.GET.get("symbol", "").strip()
        result = self.request.GET.get("result", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if symbol:
            qs = qs.filter(symbol__icontains=symbol)
        if result == "Gain":
            qs = qs.filter(pnl__gt=0)
        elif result == "Loss":
            qs = qs.filter(pnl__lt=0)
        elif result == "Zero":
            qs = qs.filter(pnl=0)
        if date_from:
            qs = qs.filter(trade_date__gte=date_from)
        if date_to:
            qs = qs.filter(trade_date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        summary = Trade.objects.aggregate(
            total=Count("id"),
            pnl_total=Sum("pnl"),
            avg_r=Avg("r_multiple"),
        )
        ctx["summary"] = summary
        ctx["filters"] = self.request.GET
        return ctx


class TradeCreateView(LoginRequiredMixin, CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "journal/trade_form.html"
    success_url = reverse_lazy("journal:dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["setup_choices"] = _setup_choices()
        kwargs["emotion_choices"] = _emotion_choices()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        last_trade = Trade.objects.exclude(market_context="").order_by("-trade_date", "-id").first()
        if last_trade and last_trade.market_context:
            initial["market_context"] = last_trade.market_context
        initial["symbol"] = "Mini Índice"
        return initial

    def form_valid(self, form):
        trade = form.save(commit=False)
        if trade.setup and trade.setup != NEW_OPTION and not JournalOption.objects.filter(kind="setup", label=trade.setup).exists():
            JournalOption.objects.create(kind="setup", label=trade.setup)
        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            value = getattr(trade, key)
            if value and value != NEW_OPTION and not JournalOption.objects.filter(kind="emotion", label=value).exists():
                JournalOption.objects.create(kind="emotion", label=value)
        trade = _compute_metrics(trade)
        trade.save()
        return redirect(self.success_url)


class TradeUpdateView(LoginRequiredMixin, UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = "journal/trade_form.html"
    success_url = reverse_lazy("journal:dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["setup_choices"] = _setup_choices()
        kwargs["emotion_choices"] = _emotion_choices()
        return kwargs

    def form_valid(self, form):
        trade = form.save(commit=False)
        if trade.setup and trade.setup != NEW_OPTION and not JournalOption.objects.filter(kind="setup", label=trade.setup).exists():
            JournalOption.objects.create(kind="setup", label=trade.setup)
        for key in ["emotion_before", "emotion_during", "emotion_after"]:
            value = getattr(trade, key)
            if value and value != NEW_OPTION and not JournalOption.objects.filter(kind="emotion", label=value).exists():
                JournalOption.objects.create(kind="emotion", label=value)
        trade = _compute_metrics(trade)
        trade.save()
        return redirect(self.success_url)


class TradeDeleteView(LoginRequiredMixin, DeleteView):
    model = Trade
    template_name = "journal/trade_confirm_delete.html"
    success_url = reverse_lazy("journal:dashboard")


class TradeDetailView(LoginRequiredMixin, DetailView):
    model = Trade
    template_name = "journal/trade_detail.html"
