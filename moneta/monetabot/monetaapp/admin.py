from django.contrib import admin

from .models import User, Auction, AuctionHistory, AuctionLot, Report, ReportImage, AuctionImage, AuctionFiles, AutoBid, OrderDoc

# Регистрируем модели, чтобы они были доступны в админке
admin.site.register(User)
admin.site.register(Auction)
admin.site.register(AuctionHistory)
admin.site.register(AuctionLot)
admin.site.register(Report)
admin.site.register(ReportImage)
admin.site.register(AuctionImage)
admin.site.register(AuctionFiles)
admin.site.register(AutoBid)
admin.site.register(OrderDoc)
