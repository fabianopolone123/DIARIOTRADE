from django.core.management.base import BaseCommand

from journal.models import Trade
from journal.views import _compute_metrics


class Command(BaseCommand):
    help = "Recalcula pnl, r_multiple, initial_risk e risk_reward de todos os trades."

    def handle(self, *args, **options):
        trades = Trade.objects.all()
        count = 0
        for trade in trades:
            _compute_metrics(trade)
            trade.save(update_fields=["pnl", "initial_risk", "r_multiple", "risk_reward", "duration_minutes"])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} trade(s) recalculado(s)."))
