from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser):
    BALANCE_DEFAULT = 0
    WARNINGS_DEFAULT = 0
    SUCCESFUL_TRADES_DEFAULT = 0

    USER_TYPE_CHOICES = [
        ('User', 'User'),
        ('Support', 'Support'),
        ('Seller', 'Seller'),
        ('Admin', 'Admin'),
    ]
    USER_STATUS_CHOICES = [
        ('active', 'active'),
        ('inactive', 'inactive'),
    ]
    balance = models.PositiveIntegerField(default=BALANCE_DEFAULT)
    hold_balance = models.PositiveIntegerField(default=BALANCE_DEFAULT)
    type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='User')
    username = models.CharField(max_length=20, unique=True)
    warnings = models.PositiveIntegerField(default=WARNINGS_DEFAULT)
    succesful_trades = models.PositiveIntegerField(default=SUCCESFUL_TRADES_DEFAULT)
    chat_id = models.CharField(max_length=16)
    first_name = models.CharField(max_length=16, null=True, blank=True)
    last_name = models.CharField(max_length=16, null=True, blank=True)
    father_name = models.CharField(max_length=16, null=True, blank=True)
    shipping_address = models.CharField(max_length=100, null=True, blank=True)
    shipping_index = models.CharField(max_length=10, null=True, blank=True)
    geolocation = models.CharField(max_length=100, null=True, blank=True)
    seller_description = models.TextField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES, default='active')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Auction(models.Model):
    product_type_choices = [
        ('Ювелирный', 'Ювелирный'),
        ('Историч ценный', 'Историч ценный'),
        ('Стандартный', 'Стандартный')
    ]
    product_name = models.CharField(max_length=50)
    geolocation = models.CharField(max_length=50)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=20, choices=product_type_choices, default='Стандартный')
    start_time = models.DateTimeField(default=timezone.now)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField(max_length=100)
    end_time = models.DateTimeField()
    active = models.BooleanField(default=False)
    message_id = models.PositiveIntegerField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.product_name


class AuctionHistory(models.Model):
    product_type_choices = [
        ('Ювелирный', 'Ювелирный'),
        ('Историч ценный', 'Историч ценный'),
        ('Стандартный', 'Стандартный')
    ]
    product_name = models.CharField(max_length=50)
    product_image = models.ImageField(upload_to='auction_images/', null=True, blank=True)
    geolocation = models.CharField(max_length=50)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_type = models.CharField(max_length=20, choices=product_type_choices, default='Стандартный')
    start_time = models.DateTimeField(default=timezone.now)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField(max_length=100)
    end_time = models.DateTimeField()
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions')
    ready_to_send_status = models.BooleanField(default=False)
    received_status = models.BooleanField(default=False)

    def __str__(self):
        return self.product_name


class AuctionLot(models.Model):
    lot_auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.value}"


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('user', 'Жалоба на пользователя'),
        ('seller_admin', 'Жалоба на продавца или администратора'),
    ]

    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_sent",
        null=True,
        blank=True
    )
    reported_on = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports_received",
        null=True,
        blank=True
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        null=True,
        blank=True
    )
    reason = models.CharField(
        max_length=100,
        choices=[
            ('reject', 'Отказ от получения/отправки'),
            ('harassment', 'Оскорбления'),
            ('scam', 'Мошенничество'),
            ('other', 'Другое')
        ],
        null=True,
        blank=True
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидание'),
            ('reviewed', 'Рассмотрено'),
            ('rejected', 'Отклонено'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.reported_by} - {self.reported_on}"


class ReportImage(models.Model):
    report = models.ForeignKey(
        Report,
        related_name='images',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to='report_images/', null=True, blank=True)

    def __str__(self):
        return f"Image for Report {self.report.id}"


class AuctionImage(models.Model):
    auction = models.ForeignKey(
        Auction,
        related_name='images',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to='auction_images/', null=True, blank=True)

    def __str__(self):
        return f"Image for Auction {self.auction.id}"

class AuctionFiles(models.Model):
    auction = models.ForeignKey(
        Auction,
        related_name='files',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    file = models.FileField(upload_to='auction_files')
    def __str__(self):
        return f"File for Auction {self.auction.id}"

class AutoBid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auto_bids")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="auto_bids")
    max_bid = models.DecimalField(max_digits=10, decimal_places=2)  # Максимальная ставка
    active = models.BooleanField(default=True)  # Включена ли авто-ставка
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AutoBid for {self.auction.product_name} by {self.user.username}"

class OrderDoc(models.Model):
    doc = models.FileField(upload_to='documents')
    auction = models.ForeignKey(AuctionHistory, on_delete=models.CASCADE, related_name='document')

    def __str__(self):
        return f'Document for {self.auction.product_name}'