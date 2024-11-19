from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Auction
from django.utils import timezone
from datetime import datetime
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import ReportForm, ReportImageForm, UserEditForm, CustomerEditForm, AuctionForm, AuctionImageForm
from .models import Report, ReportImage, User, AuctionHistory, AuctionImage, AuctionFiles, OrderDoc
from itertools import chain
from django.db.models import Value, CharField
from docx import Document
from django.core.files import File
import os
from django.conf import settings
from django.db import transaction

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Неверные имя пользователя или пароль.')
    return render(request, 'accounts/login.html')


@login_required
def user_dashboard(request):
    user = request.user

    # Проверка типа пользователя
    if user.type == 'User':
        # Для обычных пользователей
        return render(request, 'accounts/user_dashboard.html', {'user': user})
    elif user.type == 'Support':
        # Для пользователей типа Support
        return render(request, 'accounts/support_dashboard.html', {'user': user})
    elif user.type == 'Seller':
        # Для пользователей типа Seller
        return render(request, 'accounts/seller_dashboard.html', {'user': user})
    elif user.type == 'Admin':
        # Для пользователей типа Admin
        return render(request, 'accounts/superadmin_dashboard.html', {'user': user})
    else:
        # Если тип пользователя неизвестен, можно вернуть ошибку или редирект
        return render(request, 'accounts/error.html', {'message': 'Unknown user type'})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def repeat_auction(request):
    # Получаем текущего пользователя
    seller = request.user

    # Получаем все аукционы продавца из моделей Auction и AuctionHistory
    active_auctions = Auction.objects.filter(seller=seller)
    past_auctions = AuctionHistory.objects.filter(seller=seller)

    # Добавляем информацию о типе модели для каждого аукциона
    active_auctions = active_auctions.annotate(model_type=Value('active', output_field=CharField()))
    past_auctions = past_auctions.annotate(model_type=Value('inactive', output_field=CharField()))

    # Объединяем аукционы
    auctions = list(chain(active_auctions, past_auctions))

    context = {
        'auctions': auctions
    }

    return render(request, 'accounts/repeat_auction.html', context)


@login_required
def create_auction(request, auction_id=None, type=None):
    initial_auction = None

    # Проверяем, передан ли auction_id для автозаполнения
    if auction_id:
        if type == 'active':
            initial_auction = get_object_or_404(Auction, id=auction_id, seller=request.user)
        else:
            initial_auction = get_object_or_404(AuctionHistory, id=auction_id, seller=request.user)
    if request.method == 'POST':
        auction_form = AuctionForm(request.POST, seller=request.user, initial_auction=initial_auction)

        # Получаем список изображений из запроса
        image_files = request.FILES.getlist('image')
        files = request.FILES.getlist('file')

        if auction_form.is_valid():
            auction = auction_form.save(commit=False)
            auction.seller = request.user
            auction.geolocation = request.user.geolocation  # Автоматическая геолокация
            auction.save()

            # Сохраняем изображения
            for image in image_files:
                AuctionImage.objects.create(auction=auction, image=image)
            for file in files:
                AuctionFiles.objects.create(auction=auction, file=file)

            messages.success(request, 'Аукцион успешно создан.')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Произошла ошибка при создании аукциона.')

    else:
        auction_form = AuctionForm(seller=request.user, initial_auction=initial_auction)

    return render(request, 'accounts/create_auction.html', {
        'form': auction_form,
    })


@login_required
def manage_users(request):
    current_user = request.user
    if current_user.type == 'Admin':
        users = User.objects.exclude(id=current_user.id)  # Исключаем текущего пользователя

        if request.method == "POST":
            for user in users:
                user_id = str(user.id)
                role = request.POST.get(f"role_{user_id}")
                balance = request.POST.get(f"balance_{user_id}")
                warnings = request.POST.get(f"warnings_{user_id}")
                status = request.POST.get(f"status_{user_id}")

                if role:
                    user.type = role
                if balance:
                    user.balance = int(balance)
                if warnings:
                    user.warnings = int(warnings)
                if status:
                    user.status = status

                user.save()

            return redirect('manage_users')

        context = {
            'users': users
        }
        return render(request, 'accounts/manage_users.html', context)


@login_required
def pending_auctions(request):
    user = request.user
    if user.type == 'Admin' or user.type == 'Support':
        pending_auctions = Auction.objects.filter(active=False)
        return render(request, 'accounts/pending_auctions.html', {'pending_auctions': pending_auctions})


@login_required
@require_POST
def approve_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    auction.active = True
    auction.save()
    return redirect(reverse('pending_auctions'))


@login_required
@require_POST
def reject_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    auction.delete()
    return redirect(reverse('pending_auctions'))


@login_required
def create_report(request):
    if request.method == 'POST':
        print("Получен POST запрос для создания жалобы.")
        report_form = ReportForm(request.POST)

        # Проверка, если загружены изображения
        image_forms = []
        if 'image' in request.FILES:
            image_files = request.FILES.getlist('image')  # Получаем все файлы из request.FILES
            image_forms = [ReportImageForm(request.POST, request.FILES, instance=ReportImage()) for _ in image_files]
        else:
            print("Файлы изображений не были загружены.")

        if report_form.is_valid():
            print("Форма жалобы прошла валидацию.")
            all_valid = True

            # Проверка валидации изображений
            for img_form in image_forms:
                if not img_form.is_valid():
                    print(f"Ошибки валидации изображения: {img_form.errors}")
                    all_valid = False

            if all_valid:
                print("Все формы изображений прошли валидацию.")
                username = report_form.cleaned_data.get('username')
                try:
                    reported_user = get_object_or_404(User, username=username)
                    print(f"Пользователь для жалобы найден: {reported_user.username}")
                except Exception as e:
                    print(f"Ошибка при поиске пользователя с именем {username}: {e}")
                    messages.error(request, 'Пользователь не найден.')
                    return redirect('create_report')

                report = report_form.save(commit=False)
                report.reported_on = reported_user
                print(reported_user.type)
                if reported_user.type == 'User':
                    report_type = 'user'
                else:
                    report_type = 'seller_admin'

                report.report_type = report_type
                report.reported_by = request.user
                report.save()
                print(f"Жалоба на пользователя {reported_user.username} успешно сохранена.")

                # Сохранение изображений
                for img_form in image_forms:
                    image = img_form.save(commit=False)
                    image.report = report
                    image.save()
                    print(f"Изображение для жалобы успешно сохранено.")

                messages.success(request, 'Жалоба успешно отправлена.')
                return redirect('create_report')
            else:
                print("Некоторые формы изображений не прошли валидацию.")
                messages.error(request, 'Некоторые изображения не прошли валидацию.')
        else:
            print("Форма жалобы не прошла валидацию.")
            messages.error(request, 'Форма жалобы не прошла валидацию.')

    else:
        print("GET запрос для страницы создания жалобы.")
        report_form = ReportForm()
        image_forms = [ReportImageForm()]

    return render(request, 'accounts/create_report.html', {'report_form': report_form, 'image_forms': image_forms})


@login_required
def user_reports(request):
    user = request.user
    user_reports = Report.objects.filter(report_type='user', status='pending').exclude(reported_on=user).exclude(
        reported_by=user)
    return render(request, 'accounts/user_reports.html', {'user_reports': user_reports})


@login_required
@require_POST
def warn_user(request, user_id, report_id, report_type):
    user = get_object_or_404(User, id=user_id)
    report = get_object_or_404(Report, id=report_id)
    user.warnings = int(user.warnings) + 1
    user.save()
    report.status = 'reviewed'
    report.save()
    if report_type == 'user':
        return redirect(reverse('user_reports'))
    else:
        return redirect(reverse('admin_reports'))


@login_required
@require_POST
def ban_user(request, user_id, report_id, report_type):
    user = get_object_or_404(User, id=user_id)
    report = get_object_or_404(Report, id=report_id)
    user.status = 'inactive'
    report.status = 'reviewed'
    report.save()
    user.save()
    if report_type == 'user':
        return redirect(reverse('user_reports'))
    else:
        return redirect(reverse('admin_reports'))


@login_required
@require_POST
def decline_report(request, report_id, report_type):
    report = get_object_or_404(Report, id=report_id)
    report.status = 'rejected'
    report.save()
    if report_type == 'user':
        return redirect(reverse('user_reports'))
    else:
        return redirect(reverse('admin_reports'))


@login_required
def admin_reports(request):
    user = request.user
    user_reports = Report.objects.filter(report_type='seller_admin', status='pending').exclude(
        reported_on=user).exclude(reported_by=user)
    return render(request, 'accounts/admin_reports.html', {'user_reports': user_reports})


@login_required
def edit_seller(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/edit_seller.html', {'form': form})


@login_required
def edit_customer(request):
    user = request.user
    if request.method == 'POST':
        form = CustomerEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard')
    else:
        form = CustomerEditForm(instance=user)
    return render(request, 'accounts/edit_customer.html', {'form': form})


@login_required
def customers(request):
    user = request.user
    ended_auctions = AuctionHistory.objects.filter(seller=user, ready_to_send_status=True)
    return render(request, 'accounts/customers.html', {'auctions': ended_auctions})


@login_required
def orders(request):
    user = request.user
    user_orders = AuctionHistory.objects.filter(winner=user, ready_to_send_status=False)
    return render(request, 'accounts/orders.html', {'auctions': user_orders})


@login_required
def submit_order(request, auction_id):
    print(settings.BASE_DIR)
    order = get_object_or_404(AuctionHistory, id=auction_id)
    order.ready_to_send_status = True
    order.save()

    seller = order.seller
    winner = order.winner

    seller_name = f"{seller.first_name or ''} {seller.last_name or ''} {seller.father_name or ''}".strip()
    winner_name = f"{winner.first_name or ''} {winner.last_name or ''} {winner.father_name or ''}".strip()

    product_name = order.product_name
    product_type = order.product_type

    template_paths = {
        'Ювелирный': os.path.join(settings.BASE_DIR, 'monetaapp', 'templates', 'jewelry_template.docx'),
        'Историч ценный': os.path.join(settings.BASE_DIR, 'monetaapp', 'templates', 'historical_template.docx'),
        'Стандартный': os.path.join(settings.BASE_DIR, 'monetaapp', 'templates', 'standard_template.docx'),
    }

    template_path = template_paths.get(product_type)
    if not template_path or not os.path.exists(template_path):
        raise ValueError(f"Шаблон для типа {product_type} не найден.")

    document = Document(template_path)
    for paragraph in document.paragraphs:
        if "{{product_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{product_name}}", product_name)
        if "{{seller_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{seller_name}}", seller_name)
        if "{{winner_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{winner_name}}", winner_name)

    temp_file_path = f"generated_documents/order_{auction_id}.docx"
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    document.save(temp_file_path)

    with open(temp_file_path, 'rb') as file:
        OrderDoc.objects.create(
            auction=order,
            doc=File(file, name=os.path.basename(temp_file_path))
        )

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    return redirect('orders')


@login_required
def auction_history(request):
    user = request.user
    auctions = AuctionHistory.objects.filter(seller=user, received_status=True)
    return render(request, 'accounts/auction_history.html', {'auctions': auctions})


@login_required
def unreceived_orders(request):
    user = request.user
    auctions = AuctionHistory.objects.filter(winner=user, ready_to_send_status=True, received_status=False)
    return render(request, 'accounts/unreceived_orders.html', {'auctions': auctions})


@login_required
def order_received(request, auction_id):
    try:
        with transaction.atomic():
            user = request.user
            order = get_object_or_404(AuctionHistory, id=auction_id)
            order.received_status = True
            user.succesful_trades += 1
            seller = order.seller
            seller.balance += order.final_price
            user.save()
            order.save()
            seller.save()
    except Exception:
        print(f'Ошибка при подтверждении получения заказа {order.id}')
    return redirect('unreceived_orders')


@login_required
def my_reports(request):
    user = request.user
    reports = Report.objects.filter(reported_by=user)
    return render(request, 'accounts/my_reports.html', {'reports': reports})


@login_required
def orders_history(request):
    user = request.user
    auctions = AuctionHistory.objects.filter(winner=user, received_status=True)
    return render(request, 'accounts/orders_history.html', {'auctions': auctions})

@login_required
def active_auctions(request):
    user = request.user
    auctions = Auction.objects.filter(seller=user, active=True)
    return render(request, 'accounts/active_auctions.html', {'auctions': auctions})

@login_required
def stop_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    if request.user != auction.seller:
        messages.error(request, "Вы не можете завершить этот аукцион.")
        return redirect('active_auctions')

    try:
        with transaction.atomic():
            seller = auction.seller
            fee = int(float(auction.current_price) * 0.05)

            if seller.balance >= fee:
                seller.balance -= fee
                seller.save()
                auction.delete()
                messages.success(request, "Аукцион успешно завершен.")
            else:
                messages.error(request, "Недостаточно средств для завершения аукциона.")
    except Exception as e:
        messages.error(request, f"Произошла ошибка: {e}")

    return redirect('active_auctions')
