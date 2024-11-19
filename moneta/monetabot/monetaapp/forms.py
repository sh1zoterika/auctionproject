from django import forms
from .models import Report, ReportImage, User, Auction, AuctionImage, AuctionFiles
from django.utils.timezone import now


class ReportForm(forms.ModelForm):
    username = forms.CharField(label="Имя пользователя нарушителя", max_length=150)

    class Meta:
        model = Report
        fields = ['username', 'reason', 'description']


class ReportImageForm(forms.ModelForm):
    image = forms.ImageField(label='Изображение')

    class Meta:
        model = ReportImage
        fields = ['image']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['seller_description', 'geolocation', 'first_name', 'last_name', 'father_name']
        widgets = {
            'seller_description': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
            'geolocation': forms.TextInput(attrs={'placeholder': 'Введите геолокацию'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'seller_description': 'Описание продавца',
            'geolocation': 'Геолокация',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'father_name': 'Отчество'
        }


class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'father_name', 'shipping_address', 'shipping_index']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_index': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = [
            'product_name',
            'product_type',
            'description',
            'start_time',
            'end_time',
            'current_price',
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'product_name': 'Название продукта',
            'product_type': 'Тип продукта',
            'description': 'Описание',
            'start_time': 'Время начала',
            'end_time': 'Время завершения',
            'current_price': 'Текущая цена',
        }

    def __init__(self, *args, **kwargs):
        seller = kwargs.pop('seller', None)
        initial_auction = kwargs.pop('initial_auction', None)
        super().__init__(*args, **kwargs)


        if initial_auction:
            self.fields['product_name'].initial = initial_auction.product_name
            self.fields['product_type'].initial = initial_auction.product_type
            self.fields['description'].initial = initial_auction.description
            self.fields['start_time'].initial = now()
            self.fields['end_time'].initial = None


        self.fields['current_price'].initial = None

        if seller:
            pass


class AuctionImageForm(forms.ModelForm):
    image = forms.ImageField(label='Изображение')

    class Meta:
        model = AuctionImage
        fields = ['image']


class AuctionFileForm(forms.ModelForm):
    file = forms.FileField(label='Файл')

    class Meta:
        model = AuctionFiles
        fields = ['file']
