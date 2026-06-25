from django.urls import path

from .views import DashboardView, TradeCreateView, TradeDeleteView, TradeDetailView, TradeUpdateView

app_name = "journal"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("trades/new/", TradeCreateView.as_view(), name="trade_create"),
    path("trades/<int:pk>/", TradeDetailView.as_view(), name="trade_detail"),
    path("trades/<int:pk>/edit/", TradeUpdateView.as_view(), name="trade_update"),
    path("trades/<int:pk>/delete/", TradeDeleteView.as_view(), name="trade_delete"),
]
