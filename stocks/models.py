import logging
from datetime import date, datetime

from django.db import models

from utils.nse_bhav import Nse

logger = logging.getLogger(__name__)


class Stock(models.Model):
    symbol = models.CharField(max_length=100, verbose_name="Symbol")
    isin = models.CharField(max_length=30, verbose_name="ISIN")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Stock created at")

    def __str__(self):
        return self.symbol


class StockHistoryManager(models.Manager):
    def update_stocks(self, by_trade_date=date.today()):
        symbols_instance = Stock.objects.all().values('id', 'symbol')
        symbols = {stock['symbol']: stock['id'] for stock in symbols_instance}
        today_stocks = Nse(by_trade_date).data()

        stocks_history = []

        for stock in today_stocks:
            stock_id = symbols.get(stock['SYMBOL'])
            if not stock_id:
                stock_instance = Stock.objects.create(symbol=stock['SYMBOL'], isin=stock['ISIN'])
                stock_id = stock_instance.id

            stocks_history.append(self.model(stock_id=stock_id,
                                             open=stock['OPEN'], high=stock['HIGH'], low=stock['LOW'],
                                             close=stock['CLOSE'], last=stock['LAST'], prev_close=stock['PREVCLOSE'],
                                             total_traded_qty=stock['TOTTRDQTY'], total_traded_value=stock['TOTTRDVAL'],
                                             trade_date=stock['TRADEDDATE'], total_trades=stock['TOTALTRADES'],
                                             deliverables=stock['DELIVERABLES'], is_filtered=stock['is_filtered']))

        if stocks_history:
            StockHistory.objects.bulk_create(stocks_history)
        else:
            # for cron logs
            print "[%s] No data found on NSE" % datetime.now()

            logger.info("No data found on NSE")


class StockHistory(models.Model):
    stock = models.ForeignKey(Stock)
    created_at = models.DateTimeField(auto_now_add=True)
    trade_date = models.DateField(verbose_name="Traded date")
    open = models.FloatField(verbose_name="Open price")
    high = models.FloatField(verbose_name="High price")
    low = models.FloatField(verbose_name="Low price")
    close = models.FloatField(verbose_name="Close price")
    last = models.FloatField(verbose_name="Last price")
    prev_close = models.FloatField(verbose_name="Previous Close price")
    total_traded_qty = models.IntegerField(verbose_name="Total Traded quantity")
    total_traded_value = models.FloatField(verbose_name="Total Traded value")
    total_trades = models.IntegerField(verbose_name="Total Trades")
    deliverables = models.FloatField(null=True, blank=True)
    watch_list = models.BooleanField(default=False)
    is_filtered = models.BooleanField(default=False)

    # comments = models.CharField(max_length=500)

    def __str__(self):
        return '%d - %s' % (self.id, self.stock.symbol)

    objects = StockHistoryManager()
