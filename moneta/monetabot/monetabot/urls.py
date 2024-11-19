"""
URL configuration for monetabot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from monetaapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/create_auction/', views.create_auction, name='create_auction'),
    path('dashboard/manage_users', views.manage_users, name='manage_users'),
    path('dashboard/pending_auctions/', views.pending_auctions, name='pending_auctions'),
    path('dashboard/approve_auction/<int:auction_id>/', views.approve_auction, name='approve_auction'),
    path('dashboard/reject_auction/<int:auction_id>/', views.reject_auction, name='reject_auction'),
    path('dashboard/create_report/', views.create_report, name='create_report'),
    path('dashboard/warn_user/<int:user_id>&<int:report_id>&<str:report_type>/', views.warn_user, name='warn_user'),
    path('dashboard/ban_user/<int:user_id>&<int:report_id>&<str:report_type>/', views.ban_user, name='ban_user'),
    path('dashboard/decline_report/<int:report_id>&<str:report_type>/', views.decline_report, name='decline_report'),
    path('dashboard/user_reports', views.user_reports, name='user_reports'),
    path('dashboard/admin_reports', views.admin_reports, name='admin_reports'),
    path('dashboard/edit_seller/', views.edit_seller, name='edit_seller'),
    path('dashboard/edit_customer/', views.edit_customer, name='edit_customer'),
    path('dashboard/create_auction/<int:auction_id>&<str:type>/', views.create_auction, name='create_auction_with_id'),
    path('dashboard/repeat_auction/', views.repeat_auction, name='repeat_auction'),
    path('dashboard/orders', views.orders, name='orders'),
    path('dashboard/submit_order/<int:auction_id>', views.submit_order, name='submit_order'),
    path('dashboard/customers', views.customers, name='customers'),
    path('dashboard/auction_history', views.auction_history, name='auction_history'),
    path('dashboard/unreceived_orders', views.unreceived_orders, name='unreceived_orders'),
    path('dashboard/order_received/<int:auction_id>', views.order_received, name='order_received'),
    path('dashboard/my_reports', views.my_reports, name='my_reports'),
    path('dashboard/orders_history', views.orders_history, name='orders_history'),
    path('dashboard/active_auctions', views.active_auctions, name='active_auctions'),
    path('dashboard/stop_auction/<int:auction_id>', views.stop_auction, name='stop_auction')
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
