from collections import OrderedDict, defaultdict
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import NEW_OPTION, TradeForm
from .models import JournalOption, Trade

WEEKDAY_LABELS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
R_BUCKETS = [
    ("< -2R", lambda r: r < -2),
    ("-2R a -1R", lambda r: -2 <= r < -1),
    ("-1R a 0R", lambda r: -1 <= r < 0),
    ("0R a 1R", lambda r: 0 <= r < 1),
    ("1R a 2R", lambda r: 1 <= r < 2),
    ("2R a 3R", lambda r: 2 <= r < 3),
    ("> 3R", lambda r: r >= 3),
]
EXECUTION_GRADE_ORDER = ["A+", "A", "B", "C", "D"]


def _compute_metrics(trade):
    entry = trade.entry_price or Decimal("0")
    exit_price = trade.exit_price if trade.exit_price is not None else entry
    qty = trade.quantity or Decimal("0")
    point_value = trade.point_value if trade.point_value is not None else Decimal("1")
    fee_per_contract = trade.fee_per_contract if trade.fee_per_contract is not None else Decimal("0")
    stop_points = abs(trade.stop_loss or Decimal("0"))
    target_points = abs(trade.target_price or Decimal("0"))
    fees = fee_per_contract * qty
    trade.fees = fees
    side = Decimal("1") if trade.direction == "Compra" else Decimal("-1")

    if trade.target_points_net is not None:
        net_points = abs(trade.target_points_net)
    elif trade.stop_points_net is not None:
        net_points = -abs(trade.stop_points_net)
    else:
        net_points = None

    if net_points is not None:
        pnl = (net_points * qty * point_value) - fees
    else:
        pnl = ((exit_price - entry) * qty * side) - fees
    initial_risk = stop_points * qty * point_value
    planned_reward = target_points * qty * point_value
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

    SORT_FIELDS = {
        "date": "trade_date",
        "time": "entry_time",
        "symbol": "symbol",
        "direction": "direction",
        "result": "result",
        "setup": "setup",
        "quantity": "quantity",
        "target_points_net": "target_points_net",
        "stop_points_net": "stop_points_net",
    }
    SORT_COLUMNS = [
        ("date", "Data"),
        ("time", "Hora"),
        ("symbol", "Ativo"),
        ("direction", "Dir"),
        ("result", "Resultado"),
        ("setup", "Setup"),
        ("quantity", "Qtd"),
        ("target_points_net", "Pontos líquidos"),
        ("stop_points_net", "Stop líquido"),
    ]

    def get_queryset(self):
        qs = Trade.objects.all()
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

        sort = self.request.GET.get("sort", "date")
        direction = self.request.GET.get("dir", "desc")
        field = self.SORT_FIELDS.get(sort, "trade_date")
        order_field = field if direction == "asc" else f"-{field}"
        return qs.order_by(order_field, "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        summary = Trade.objects.aggregate(
            total=Count("id"),
            pnl_total=Sum("pnl"),
            avg_r=Avg("r_multiple"),
        )
        ctx["summary"] = summary
        ctx["filters"] = self.request.GET

        current_sort = self.request.GET.get("sort", "date")
        current_dir = self.request.GET.get("dir", "desc")
        headers = []
        for key, label in self.SORT_COLUMNS:
            active = current_sort == key
            next_dir = "asc" if active and current_dir == "desc" else "desc"
            params = self.request.GET.copy()
            params["sort"] = key
            params["dir"] = next_dir
            headers.append(
                {
                    "label": label,
                    "url": f"?{params.urlencode()}",
                    "active": active,
                    "dir": current_dir if active else "",
                }
            )
        ctx["headers"] = headers
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
        last_trade = Trade.objects.order_by("-trade_date", "-id").first()
        last_trade_with_context = Trade.objects.exclude(market_context="").order_by("-trade_date", "-id").first()
        if last_trade:
            initial["quantity"] = last_trade.quantity
            initial["point_value"] = last_trade.point_value
            initial["fee_per_contract"] = last_trade.fee_per_contract
            initial["stop_loss"] = last_trade.stop_loss
            initial["target_price"] = last_trade.target_price
        if last_trade_with_context and last_trade_with_context.market_context:
            initial["market_context"] = last_trade_with_context.market_context
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


class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "journal/report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trades = list(Trade.objects.all().order_by("trade_date", "entry_time", "id"))

        def f(value):
            return float(value) if value is not None else 0.0

        total = len(trades)
        wins = [t for t in trades if f(t.pnl) > 0]
        losses = [t for t in trades if f(t.pnl) < 0]
        zeros = [t for t in trades if f(t.pnl) == 0]
        win_rate = (len(wins) / total * 100) if total else 0
        gross_profit = sum(f(t.pnl) for t in wins)
        gross_loss = sum(f(t.pnl) for t in losses)
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss else None
        expectancy = (sum(f(t.pnl) for t in trades) / total) if total else 0
        avg_r = (sum(f(t.r_multiple) for t in trades) / total) if total else 0
        best_trade = max((f(t.pnl) for t in trades), default=0)
        worst_trade = min((f(t.pnl) for t in trades), default=0)
        avg_duration = (sum(t.duration_minutes for t in trades) / total) if total else 0

        longest_win_streak = longest_loss_streak = 0
        current_streak_type = None
        streak = 0
        prev_sign = None
        for t in trades:
            pnl = f(t.pnl)
            sign = "win" if pnl > 0 else ("loss" if pnl < 0 else None)
            if sign is None:
                streak = 0
                prev_sign = None
                continue
            streak = streak + 1 if sign == prev_sign else 1
            prev_sign = sign
            if sign == "win":
                longest_win_streak = max(longest_win_streak, streak)
            else:
                longest_loss_streak = max(longest_loss_streak, streak)
        current_streak_count = streak if trades else 0
        if trades:
            current_streak_type = prev_sign

        equity_labels, equity_values = [], []
        cumulative = 0.0
        for t in trades:
            cumulative += f(t.pnl)
            equity_labels.append(t.trade_date.strftime("%d/%m"))
            equity_values.append(round(cumulative, 2))

        result_counts = OrderedDict([("Gain", len(wins)), ("Loss", len(losses)), ("Zero", len(zeros))])

        def grouped_rows(key_func, filter_func=None):
            stats = defaultdict(lambda: {"pnl": 0.0, "wins": 0, "count": 0})
            for t in trades:
                if filter_func and not filter_func(t):
                    continue
                key = key_func(t)
                s = stats[key]
                s["pnl"] += f(t.pnl)
                s["count"] += 1
                if f(t.pnl) > 0:
                    s["wins"] += 1
            rows = [
                {
                    "label": k,
                    "avg_pnl": round(v["pnl"] / v["count"], 2),
                    "win_rate": round(v["wins"] / v["count"] * 100, 1),
                    "count": v["count"],
                }
                for k, v in stats.items()
            ]
            return sorted(rows, key=lambda r: r["avg_pnl"])

        setup_rows = grouped_rows(lambda t: t.setup or "Sem setup")
        emotion_rows = grouped_rows(lambda t: t.emotion_during, filter_func=lambda t: t.emotion_during)

        weekday_pnl = [0.0] * 7
        weekday_count = [0] * 7
        for t in trades:
            idx = t.trade_date.weekday()
            weekday_pnl[idx] += f(t.pnl)
            weekday_count[idx] += 1

        direction_rows = grouped_rows(lambda t: t.direction)

        def compare_bool(field, true_label, false_label):
            groups = {True: {"pnl": 0.0, "wins": 0, "count": 0}, False: {"pnl": 0.0, "wins": 0, "count": 0}}
            for t in trades:
                g = groups[bool(getattr(t, field))]
                g["pnl"] += f(t.pnl)
                g["count"] += 1
                if f(t.pnl) > 0:
                    g["wins"] += 1
            rows = []
            for key, label in [(True, true_label), (False, false_label)]:
                g = groups[key]
                rows.append(
                    {
                        "label": label,
                        "avg_pnl": round(g["pnl"] / g["count"], 2) if g["count"] else 0,
                        "win_rate": round(g["wins"] / g["count"] * 100, 1) if g["count"] else 0,
                        "count": g["count"],
                    }
                )
            return rows

        planned_rows = compare_bool("planned_trade", "Planejado", "Não planejado")
        followed_rows = compare_bool("followed_plan", "Seguiu o plano", "Não seguiu o plano")

        bucket_counts = [0] * len(R_BUCKETS)
        for t in trades:
            r = f(t.r_multiple)
            for i, (_, test) in enumerate(R_BUCKETS):
                if test(r):
                    bucket_counts[i] += 1
                    break

        grade_stats = defaultdict(lambda: {"pnl": 0.0, "count": 0})
        for t in trades:
            if not t.execution_grade:
                continue
            g = grade_stats[t.execution_grade]
            g["pnl"] += f(t.pnl)
            g["count"] += 1
        grade_rows = [
            {
                "label": grade,
                "avg_pnl": round(grade_stats[grade]["pnl"] / grade_stats[grade]["count"], 2),
                "count": grade_stats[grade]["count"],
            }
            for grade in EXECUTION_GRADE_ORDER
            if grade_stats[grade]["count"]
        ]

        ctx["summary"] = {
            "total": total,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
            "expectancy": round(expectancy, 2),
            "avg_r": round(avg_r, 2),
            "best_trade": round(best_trade, 2),
            "worst_trade": round(worst_trade, 2),
            "avg_duration": round(avg_duration),
            "longest_win_streak": longest_win_streak,
            "longest_loss_streak": longest_loss_streak,
            "current_streak_type": current_streak_type,
            "current_streak_count": current_streak_count,
        }
        ctx["setup_rows"] = setup_rows
        ctx["emotion_rows"] = emotion_rows
        ctx["direction_rows"] = direction_rows
        ctx["planned_rows"] = planned_rows
        ctx["followed_rows"] = followed_rows
        ctx["grade_rows"] = grade_rows
        ctx["worst_setups"] = [r for r in setup_rows if r["avg_pnl"] < 0][:3]
        ctx["worst_emotions"] = [r for r in emotion_rows if r["avg_pnl"] < 0][:3]

        ctx["chart_data"] = {
            "equity": {"labels": equity_labels, "values": equity_values},
            "result": {"labels": list(result_counts.keys()), "values": list(result_counts.values())},
            "setup": {
                "labels": [r["label"] for r in setup_rows],
                "avg_pnl": [r["avg_pnl"] for r in setup_rows],
            },
            "weekday": {"labels": WEEKDAY_LABELS, "pnl": [round(v, 2) for v in weekday_pnl]},
            "direction": {
                "labels": [r["label"] for r in direction_rows],
                "win_rate": [r["win_rate"] for r in direction_rows],
            },
            "emotion": {
                "labels": [r["label"] for r in emotion_rows],
                "avg_pnl": [r["avg_pnl"] for r in emotion_rows],
            },
            "r_buckets": {"labels": [b[0] for b in R_BUCKETS], "values": bucket_counts},
            "grade": {"labels": [r["label"] for r in grade_rows], "avg_pnl": [r["avg_pnl"] for r in grade_rows]},
        }
        return ctx
