from django.shortcuts import render, get_object_or_404, redirect
from .models import (
    Product,
    Category,
    Order,
    OrderProduct,
    Attribute,
    AttributeValue,
    ProductImage,
    ProductSize,
)
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from custom_login.models import Profile
from .form import Edit
from core import settings
import requests
import json
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from .models import Discount
from django.db.models import Sum
from django.db.models import Prefetch
import base64
import random

# Create your views here.


def index(request):
    initial_limit = 0
    sort = request.GET.get("sort")
    products = (
        Product.objects.defer(
            "content",
            "category",
            "seo_title",
            "meta",
            "date_created",
            "modified_date",
            "content_code",
        )
        .filter(status=True)
        .prefetch_related("sizes")
    )
    if sort == "new_to_old":
        products = products.order_by("-created_at", "-id")
    elif sort == "old_to_new":
        products = products.order_by("created_at", "id")
    else:
        products = products.order_by("-created_at", "-id")

    products = products[:initial_limit]
    products_data = []

    for product in products:
        sizes = list(product.sizes.all())
        products_data.append(
            {
                "product": product,
                "product_size": sizes[0] if sizes else None,
                "product_size_stocks": sum(
                    size.stock for size in sizes if size.stock is not None
                ),
            }
        )
    return render(
        request, "index.html", {"products": products, "products_data": products_data}
    )


def store(request, title: str):
    category = get_object_or_404(Category, title=title)
    sort = request.GET.get("sort")
    filter = request.GET.get("content")
    products = (
        Product.objects.defer(
            "content",
            "category",
            "seo_title",
            "meta",
            "date_created",
            "modified_date",
            "content_code",
        )
        .filter(status=True, category=category)
        .annotate(stock=Sum("sizes__stock"))
        .filter(stock__gt=0)
        .prefetch_related("sizes")
    )
    if sort == "new_to_old":
        products = products.order_by("-created_at", "-id")
    elif sort == "old_to_new":
        products = products.order_by("created_at", "id")
    else:
        products = products.order_by("-created_at", "-id")

    if filter:
        products = products.filter(content__icontains=filter)

    products_data = []
    paginator = Paginator(products, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    for product in page_obj:
        sizes = list(product.sizes.all())
        products_data.append(
            {
                "product": product,
                "product_size": sizes[0] if sizes else None,
                "product_size_stocks": sum(
                    size.stock for size in sizes if size.stock is not None
                ),
            }
        )
    return render(
        request,
        "store.html",
        {
            "products": products,
            "category": category,
            "products_data": products_data,
            "page_obj": page_obj,
            "sort": sort,
            "filter": filter,
        },
    )


def product(request, product_slug: str):
    product = get_object_or_404(
        Product.objects.prefetch_related("images"), product_slug=product_slug
    )

    related_products = (
        Product.objects.filter(content_code=product.content_code, status=True)
        .exclude(pk=product.pk)
        .prefetch_related(Prefetch("sizes", to_attr="prefetched_sizes"))
    )

    related_products_data = []
    for related_product in related_products:
        product_size = (
            related_product.prefetched_sizes[0]
            if related_product.prefetched_sizes
            else None
        )
        related_products_data.append(
            {"product": related_product, "product_size": product_size}
        )

    return render(
        request,
        "product.html",
        {
            "product": product,
            "related_products_data": related_products_data,
            "product_images": product.images.all(),
        },
    )


def get_snapppay_jwt_token():
    url = f"{settings.SNAPPPAY_API_BASE}/api/online/v1/oauth/token"

    auth_string = f"{settings.SNAPPPAY_CLIENT_ID}:{settings.SNAPPPAY_CLIENT_SECRET}"

    auth_header = {
        "Authorization": f"Basic {base64.b64encode(auth_string.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "password",
        "scope": "online-merchant",
        "username": settings.SNAPPPAY_USERNAME,
        "password": settings.SNAPPPAY_PASSWORD,
    }

    response = requests.post(url, data=data, headers=auth_header, timeout=10)
    try:
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except requests.exceptions.RequestException:
        return None


def check_snapppay_eligibility(jwt_token, amount):
    url = f"{settings.SNAPPPAY_API_BASE}/api/online/offer/v1/eligible?amount={int(amount)*10}"

    headers = {"Authorization": f"Bearer {jwt_token}"}

    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("response", {}).get("eligible", False)
        return False
    except requests.exceptions.RequestException:
        return False
        

def check_snapppay_eligibility_and_display(jwt_token, amount):
    url = f"{settings.SNAPPPAY_API_BASE}/api/online/offer/v1/eligible?amount={int(amount)*10}"

    headers = {"Authorization": f"Bearer {jwt_token}"}

    try:
        response = requests.get(url=url, headers=headers, timeout=10)
        if response.status_code == 200:
            eligible = response.json().get("response", {}).get("eligible", False)
            title_message = response.json().get("response", {}).get("title_message")
            description = response.json().get("response", {}).get("description")
            return {"eligible": eligible, "title_message": title_message, "description": description}
        return {"eligible": False, "title_message": "", "description": ""}
    except requests.exceptions.RequestException:
        return {"eligible": False, "title_message": "", "description": ""}
        
        
def generate_snapppay_transaction_id():
    transaction_chars = []
    transaction_id = ""
    for char in range(1, 11):
        transaction_chars.append(str(random.randint(1, 9)))
    
    for char in transaction_chars:
        transaction_id += char

    return transaction_id
    

def snapppay_get_payment_status(jwt_token, payment_token):
    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/status?paymentToken={payment_token}"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            transaction_id = response.json().get("response", {}).get("transactionId")
            status = response.json().get("response", {}).get("status")
            amount = response.json().get("response", {}).get("amount")
            success = response.json().get("successful")
            return {"transaction_id": transaction_id, "status": status, "amount": amount, "success": success, "verify_alt": True}
        return {"error": "مشکلی در استعلام وضعیت سفارش و فرایند خرید وجود دارد. اسنپ پی پاسخ نمی دهد."}
    except requests.exceptions.RequestException:
        return {"error": "مشکلی در استعلام وضعیت سفارش و فرایند خرید وجود دارد. اسنپ پی پاسخ نمی دهد."}
    

@login_required(login_url="register")
def checkout(request):
    shipping_and_total = 0
    try:
        Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect(reverse("register"))
    if request.method == "POST":
        cart = request.session.get("cart", {})
        total = 0
        discount = []
        if cart:
            for item in cart.values():
                sub_total = item["quantity"] * item["price"]
                total += sub_total
            shipping_and_total = 75000 + total
            discount_amount = 0
            discount_code = request.POST.get("discount_code")
            if discount_code:
                discount = Discount.objects.filter(
                    code=discount_code, is_active=True
                ).first()
                if discount and discount.is_valid():
                    if total > discount.min_purchase:
                        if discount.discount_percent:
                            for discount_item in cart.values():
                                discount_amount += discount_item["price"] * (discount.discount_percent / 100) * discount_item["quantity"]
                        elif discount.discount_amount:
                            discount_amount = discount.discount_amount
            if discount_amount > 0:
                total -= discount_amount
                shipping_and_total = total + 75000
            payment_method = request.POST.get("payment_method")
            order = Order.objects.create(
                user=request.user,
                total_price=shipping_and_total,
                order_user_name=request.user.username,
                order_mobile=request.user.mobile,
                order_address=request.user.profile.address,
                order_city=request.user.profile.city,
                order_name=request.user.profile.name,
                status="FA",
                payment_method=payment_method,
                order_discount= int(discount_amount) if discount_amount > 0 else 0,
                order_discount_code=discount_code
            )
            for item in cart.values():
                if discount and discount.discount_percent:
                    order_item_discount = item["price"] * (discount.discount_percent / 100) * item["quantity"]
                else:
                    order_item_discount = 0
                OrderProduct.objects.create(
                    order=order,
                    product_id=int(item["product_id"]),
                    quantity=item["quantity"],
                    price=item["price"],
                    size_id=int(item["size_id"]),
                    order_item_discount=int(order_item_discount)
                )
                

            if payment_method == "snapppay":
                jwt_token = get_snapppay_jwt_token()
                if not jwt_token:
                    return render(
                        request,
                        "checkout.html",
                        {"error": f"No JWT Token Found. Error: {jwt_token}"},
                    )

                eligible = check_snapppay_eligibility(jwt_token, shipping_and_total)
                if eligible:
                    return redirect(reverse("snapppay_gateway", args=[order.pk]))
                else:
                    return render(
                        request,
                        "checkout.html",
                        {"error": f"Not Eligible. Token: {jwt_token}"},
                    )

            return redirect(reverse("bank-gateway", args=[order.pk]))
    cal_cart = request.session.get("cart")
    pure_total_price = 0
    sub = 0
    shipping_and_total_for_snapppay_display = 0
    for value in cal_cart.values():
        product_size = ProductSize.objects.get(pk=value["size_id"])
        product_price = product_size.price
        product_quantity = value["quantity"]
        sub = product_price * product_quantity
        pure_total_price += sub
        
    for value in cal_cart.values():
        shipping_and_total_for_snapppay_display += value["price"]
    shipping_and_total_for_snapppay_display = shipping_and_total_for_snapppay_display + 75000
    jwt_token_for_snapppay_display = get_snapppay_jwt_token()
    if jwt_token_for_snapppay_display:
        res = check_snapppay_eligibility_and_display(jwt_token_for_snapppay_display, shipping_and_total_for_snapppay_display)
        title_message_for_snapppay_display = res["title_message"]
        description_for_snapppay_display = res["description"]
    return render(request, "checkout.html", {"pure_total_price": pure_total_price, "title_message_for_snapppay_display": title_message_for_snapppay_display, "description_for_snapppay_display": description_for_snapppay_display})


@login_required(login_url="register")
def snapppay_payment_settle(order):
    if not order.snapppay_payment_token:
        return False, "No Payment Token Found"

    jwt_token = get_snapppay_jwt_token()

    if not jwt_token:
        return False, "No JWT Token Found"

    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/settle"

    data = {"paymentToken": order.snapppay_payment_token}

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        try:
            successful = response.json().get("successful")
            transaction_id = response.json().get("response", {}).get("transactionId")
            if successful:
                if order.snapppay_transaction_id != transaction_id:
                    return False, "Transaction ID Mismatch"
                return True, None
            else:
                return False, "Not Successful"
        except ValueError:
            return False, "Value Error"
    except requests.exceptions.RequestException as e:
        return False, f"{str(e)}"


@csrf_exempt
def snapppay_payment_result(request):
    state = request.POST.get("state")
    amount = request.POST.get("amount")
    transactionId = request.POST.get("transactionId")
    if state != "OK":
        return render(
            request, "snapppay_result.html", {"error": "مشکلی در پرداخت پیش آمده"}
        )
    return render(
        request,
        "snapppay_result.html",
        {"state": state, "amount": amount, "transactionId": transactionId},
    )


@csrf_exempt
def snapppay_payment_verify(request):

    payment_token = request.session.get("snapppay_payment_token")

    if not payment_token:
        return render(
            request,
            "bank_gateway.html",
            {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."},
        )
    try:
        order = Order.objects.get(snapppay_payment_token=payment_token)
    except Order.DoesNotExist:
        return render(
            request,
            "bank_gateway.html",
            {"error": "هیچ سفارشی یافت نشد."},
        )

    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/verify"

    jwt_token = get_snapppay_jwt_token()

    if not jwt_token:
        return render(request, "bank_gateway.html", {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."})

    data = {"paymentToken": payment_token}

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    
    creds = {}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            successful = response.json().get("successful")
            transaction_id = response.json().get("response", {}).get("transactionId")
            if successful:
                order.snapppay_transaction_id = transaction_id
                order.save()
                settle_success, settle_error = snapppay_payment_settle(order)
                if not settle_success:
                    return render(
                        request,
                        "snapppay_verify.html",
                        {"order": order, "error": "مشکلی در نهایی کردن پرداخت پیش آمده."},
                    )
                order.status = "DO"
                order.save()
                request.session["cart"] = {}
                request.session.modified = True
                return render(request, "snapppay_verify.html", {"order": order})
            else:
                return render(
                    request,
                    "snapppay_verify.html",
                    {"order": order, "error": "پاسخ اسنپ پی موفقیت آمیز نبود."},
                )
        else:
            creds = snapppay_get_payment_status(jwt_token, payment_token)
            if "error" not in creds.keys():
                return render(request, "snapppay_verify.html", creds)
            return render(
                request,
                "bank_gateway.html",
                {"error": "خطایی در پاسخ اسنپ پی وجود دارد"},
            )
    except requests.exceptions.RequestException:
        creds = snapppay_get_payment_status(jwt_token, payment_token)
        if "error" not in creds.keys():
            return render(request, "snapppay_verify.html", creds)
        return render(request, "bank_gateway.html", {"error": "اسنپ پی پاسخ نمی دهد."})


@login_required(login_url="register")
def snapppay_payment_cancel(request, snapppay_payment_token):
    if not request.user.is_staff:
        return render(request, "snapppay_cancel.html", {"error": "شما اجازه دسترسی به این صفحه را ندارید."})

    if not snapppay_payment_token:
        return render(
            request, "snapppay_cancel.html", {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."}
        )

    jwt_token = get_snapppay_jwt_token()
    if not jwt_token:
        return render(request, "snapppay_cancel.html", {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."})

    try:
        order = Order.objects.get(snapppay_payment_token=snapppay_payment_token)
    except Order.DoesNotExist:
        return render(
            request,
            "snapppay_cancel.html",
            {"error": "هیچ سفارشی یافت نشد."},
        )

    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/cancel"

    data = {"paymentToken": snapppay_payment_token}

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        try:
            successful = response.json().get("successful")
            transaction_id = response.json().get("response", {}).get("transactionId")
            if successful:
                order.status = "SC"
                order.snapppay_transaction_id = transaction_id
                order.save()
                order_items = OrderProduct.objects.filter(order=order)
                product_size_id = 0
                product_size = 0
                for item in order_items:
                    product_size_id = item.size.pk
                    product_size = ProductSize.objects.get(pk=product_size_id)
                    product_size.stock += item.quantity
                    product_size.save()
                return render(
                    request,
                    "snapppay_cancel.html",
                    {
                        "transactionId": transaction_id,
                        "status": order.status,
                        "amount": order.total_price,
                    },
                )
            else:
                return render(
                    request,
                    "snapppay_cancel.html",
                    {"error": "پاسخ اسنپ پی موفقیت آمیز نبود."},
                )
        except Exception as e:
            return render(request, "snapppay_cancel.html", {"error": "خطایی در پاسخ اسنپ پی وجود دارد."})
    except requests.exceptions.RequestException as e:
        return render(request, "snapppay_cancel.html", {"error": "خطایی در پاسخ اسنپ پی وجود دارد."})


@login_required(login_url="register")
def snapppay_payment_update(request, order_id):
    if not request.user.is_staff:
        return render(request, "snapppay_update.html", {"error": "شما اجازه دسترسی به این صفحه را ندارید."})

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return render(request, "snapppay_update.html", {"error": "هیچ سفارشی یافت نشد."})

    jwt_token = get_snapppay_jwt_token()

    if not jwt_token:
        return render(
            request, "snapppay_update.html", {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."}
        )

    cart_list = []
    cart_total = 0
    cart_items = []
    cart_products = OrderProduct.objects.filter(order=order)
    cart_items = [
        {
            "id": product.product.pk,
            "amount": product.price * 10,
            "category": product.product.category.persian_name,
            "count": product.quantity,
            "name": product.product.title,
            "commissionType": "100",
        }
        for product in cart_products
    ]

    shipping_amount = 75000
    tax_amount = 0
    sub_total = 0
    cart_total_amount = 0
    discount_amount = 0
    for item in cart_products:
        sub_total = item.quantity * item.price
        cart_total_amount += sub_total
        discount_amount += int(item.order_item_discount)

    cart_list.append(
        {
            "cartId": order.pk,
            "cartItems": cart_items,
            "isShipmentIncluded": True,
            "isTaxIncluded": True,
            "shippingAmount": shipping_amount * 10,
            "taxAmount": tax_amount,
            "totalAmount": (cart_total_amount * 10) + 750000,
        }
    )

    external_source_amount = 0 * 10
    discount_amount_irr = discount_amount*10
    total_amount = (
        sum(cart["totalAmount"] for cart in cart_list)
        - discount_amount_irr
        - external_source_amount
    )

    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/update"

    data = {
        "amount": total_amount,
        "cartList": cart_list,
        "discountAmount": discount_amount*10,
        "externalSourceAmount": external_source_amount,
        "paymentMethodTypeDto": "INSTALLMENT",
        "paymentToken": order.snapppay_payment_token,
    }

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        try:
            successful = response.json().get("successful")
            transaction_id = response.json().get("response", {}).get("transactionId")
            if successful:
                order.snapppay_transaction_id = transaction_id
                order.status = "SU"
                order.save()
                return render(
                    request,
                    "snapppay_update.html",
                    {
                        "transactionId": transaction_id,
                        "status": order.status,
                        "amount": order.total_price,
                        "data": data
                    },
                )
            else:
                return render(
                    request, "snapppay_update.html", {"error": "پاسخ اسنپ پی موفقیت آمیز نبود."}
                )
        except Exception as e:
            return render(request, "snapppay_update.html", {"error": "خطایی در پاسخ اسنپ پی وجود دارد."})
    except requests.exceptions.RequestException as e:
        return render(request, "snapppay_update.html", {"error": "خطایی در پاسخ اسنپ پی وجود دارد."})


@login_required(login_url="register")
def snapppay_gateway(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.payment_method != "snapppay":
        return render(request, "bank_gateway.html", {"error": "روش پرداخت معتبر نیست."})

    jwt_token = get_snapppay_jwt_token()

    if not jwt_token:
        return render(
            request, "bank_gateway.html", {"error": "در حال حاضر اسنپ پی پاسخ نمی دهد. دوباره تلاش کنید."}
        )

    url = f"{settings.SNAPPPAY_API_BASE}/api/online/payment/v1/token"

    cart_list = []
    cart_total = 0
    cart_items = []
    cart_products = OrderProduct.objects.filter(order=order)
    cart_items = [
        {
            "id": product.product.pk,
            "amount": product.price * 10,
            "category": product.product.category.persian_name,
            "count": product.quantity,
            "name": product.product.title,
            "commissionType": "100",
        }
        for product in cart_products
    ]

    shipping_amount = 75000
    tax_amount = 0
    sub_total = 0
    cart_total_amount = 0
    for item in cart_products:
        sub_total = item.price * item.quantity
        cart_total_amount += sub_total

    cart_list.append(
        {
            "cartId": order.pk,
            "cartItems": cart_items,
            "isShipmentIncluded": True,
            "isTaxIncluded": True,
            "shippingAmount": shipping_amount * 10,
            "taxAmount": tax_amount,
            "totalAmount": (cart_total_amount * 10) + 750000,
        }
    )
    external_source_amount = 0 * 10
    discount_amount = (
        cart_total_amount - int(order.total_price) + (shipping_amount)
    ) * 10
    total_amount = (
        sum(cart["totalAmount"] for cart in cart_list)
        - discount_amount
        - external_source_amount
    )
    data = {
        "amount": total_amount,
        "cartList": cart_list,
        "discountAmount": discount_amount,
        "externalSourceAmount": external_source_amount,
        "mobile": f"+98{order.order_mobile[1:]}",
        "paymentMethodTypeDto": "INSTALLMENT",
        "returnURL": settings.SNAPPPAY_RETURN_URL,
        "transactionId": generate_snapppay_transaction_id(),
    }
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    payment_token = ""
    payment_page_url = ""
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            try:
                payment_token = response.json().get("response", {}).get("paymentToken")
                payment_page_url = (
                    response.json().get("response", {}).get("paymentPageUrl")
                )
                if payment_token and payment_page_url:
                    order.snapppay_payment_token = payment_token
                    request.session["snapppay_payment_token"] = payment_token
                    order.save()
                    return redirect(payment_page_url)
                else:
                    return render(
                        request,
                        "bank_gateway.html",
                        {"error": "صفحه ای یافت نشد."},
                    )
            except ValueError:
                return render(request, "bank_gateway.html", {"error": "مشکلی در پاسخ اسنپ پی وجود دارد."})
        else:
            return render(
                request,
                "bank_gateway.html",
                {"error": "مشکلی در پاسخ اسنپ پی وجود دارد."},
            )
    except requests.exceptions.RequestException as e:
        return render(request, "bank_gateway.html", {"error": f"{str(e)}"})


ZP_API_REQUEST = f"https://payment.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = f"https://payment.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = f"https://payment.zarinpal.com/pg/StartPay/"

amount = 1000  # Rial / Required
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"  # Required
phone = "YOUR_PHONE_NUMBER"  # Optional

CallbackURL = "http://artinogame.com/verify/"


@login_required
def bank_gateway(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    data = {
        "merchant_id": settings.MERCHANT,
        "amount": int(order.total_price) * 10,
        "description": f"{order.pk}",
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
    }
    data = json.dumps(data)
    headers = {"content-type": "application/json", "content-length": str(len(data))}
    try:
        response = requests.post(ZP_API_REQUEST, data=data, headers=headers, timeout=10)

        if response.status_code == 200:
            response = response.json()
            print(response)
            if response["data"]["code"] == 100:
                authority = response["data"]["authority"]
                order.gateway_bank_order_authority = authority
                order.save()
                return redirect(ZP_API_STARTPAY + authority)
            else:
                return render(
                    request,
                    "bank_gateway.html",
                    {"error": f"status code = {response['data']['code']}"},
                )
        return render(
            request,
            "bank_gateway.html",
            {
                "error": f"status code = {response.status_code} Response = {response.text}"
            },
        )

    except requests.exceptions.Timeout:
        render(request, "bank_gateway.html", {"error": "time out error"})
    except requests.exceptions.ConnectionError:
        render(request, "bank_gateway.html", {"error": "connection error"})


def verify(request):
    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if status and status != "OK":
        order = get_object_or_404(Order, gateway_bank_order_authority=authority)
        order.status = "FA"
        order.save()
        return render(
            request,
            "verify.html",
            {"order_id": order.pk, "error": "پرداخت با خطا مواجه شد"},
        )

    if status and status == "OK":
        order = get_object_or_404(Order, gateway_bank_order_authority=authority)
        order.status = "DO"
        order.save()
        request.session["cart"] = {}
        request.session.modified = True
        data = {
            "merchant_id": settings.MERCHANT,
            "amount": int(order.total_price) * 10,
            "authority": order.gateway_bank_order_authority,
        }
        data = json.dumps(data)
        headers = {"content-type": "application/json", "content-length": str(len(data))}
        try:
            response = requests.post(
                ZP_API_VERIFY, data=data, headers=headers, timeout=10
            )

            if response.status_code == 200:
                response = response.json()
                print(response)
                if response["data"]["code"] == 100:
                    ref_id = response["data"]["ref_id"]
                    order.gateway_bank_order_ref_id = ref_id
                    order.save()
                    return render(
                        request, "verify.html", {"ref_id": ref_id, "order": order}
                    )
                else:
                    return render(
                        request,
                        "verify.html",
                        {"error": f"status code = {response['data']['code']}"},
                    )
            return render(
                request,
                "verify.html",
                {
                    "error": f"status code = {response.status_code} Response = {response.text}"
                },
            )

        except requests.exceptions.Timeout:
            render(request, "verify.html", {"error": "time out error"})
        except requests.exceptions.ConnectionError:
            render(request, "verify.html", {"error": "connection error"})

    return render(request, "verify.html")


@require_http_methods(["POST"])
def add_to_cart(request):
    quantity = request.POST.get("quantity")
    product_id = request.POST.get("product")
    size_id = request.POST.get("size")
    product = get_object_or_404(Product, id=product_id)
    product_size = get_object_or_404(ProductSize, id=size_id, product=product)
    cart = request.session.get("cart")

    if not cart:
        cart = request.session["cart"] = {}

    cart_key = f"{product_id}-{size_id}"
    if cart_key in cart:
        cart[cart_key]["quantity"] += 1

    else:
        cart[cart_key] = {
            "product_id": product_id,
            "size_id": size_id,
            "quantity": int(quantity),
            "price": (
                int(product_size.discount_price)
                if product_size.discount_price
                else int(product_size.price)
            ),
            "discount_price": (
                int(product_size.price) if int(product_size.price) else None
            ),
        }

    request.session.modified = True
    return redirect(reverse("cart"))


def cart_detail(request):
    cal_cart = request.session.get("cart")
    pure_total_price = 0
    sub = 0
    changed = False
    keys_to_del = []
    products_to_del_dispaly = []
    for key, value in cal_cart.items():
        product_size = ProductSize.objects.get(pk=value["size_id"])
        product_stock = product_size.stock
        if product_stock == 0:
            keys_to_del.append(key)
        product_price = product_size.price
        product_quantity = value["quantity"]
        sub = product_price * product_quantity
        pure_total_price += sub
        
    if len(keys_to_del) > 0:
        changed = True
        
    for key in keys_to_del:
        product_id = cal_cart[key]["product_id"]
        product = Product.objects.get(pk=product_id)
        products_to_del_dispaly.append(product)
        del cal_cart[key]
    
    request.session["cart"] = cal_cart
    return render(request, "cart.html", {"pure_total_price": pure_total_price, "changed": changed, "products_to_del_dispaly": products_to_del_dispaly})


def remove_from_cart(request, cart_key):
    cart = request.session.get("cart", {})
    if cart_key in cart:
        del cart[cart_key]
        request.session.modified = True
    return redirect(request.META.get("HTTP_REFERER", reverse("index")))


@login_required(login_url="register")
def edit(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id)
    if request.user != profile.user:
        return HttpResponseForbidden("فاقد اجازه دسترسی")
    if request.method == "POST":
        form = Edit(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(reverse("checkout"))
    else:
        form = Edit(instance=profile)

    return render(request, "edit_profile.html", {"form": form})


@login_required(login_url="register")
def profile_panel(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect(reverse("register"))
    try:
        orders = Order.objects.filter(user=request.user)
    except Order.DoesNotExist:
        return render(request, "profile_panel.html", {"profile": profile})

    return render(request, "profile_panel.html", {"profile": profile, "orders": orders})


@login_required(login_url="register")
def profile_orders(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id)
    if request.user != profile.user:
        return HttpResponseForbidden("فاقد اجازه دسترسی")
    order_data = {}
    orders = Order.objects.filter(user=user_id)
    for order in orders:
        order_data[order] = OrderProduct.objects.filter(order=order)

    return render(request, "orders.html", {"order_data": order_data})


def load_more_products(request):
    try:
        limit = int(request.GET.get("limit"))
        offset = int(request.GET.get("offset"))

        products = Product.objects.defer(
            "content",
            "category",
            "seo_title",
            "meta",
            "date_created",
            "modified_date",
            "content_code",
        ).filter(status=True).prefetch_related("sizes").annotate(stock=Sum("sizes__stock")).filter(stock__gt=0).order_by("-id")

        products = products[offset : offset + limit]

        products_data = []

        for product in products:
            available_stocks = []
            sizes = list(product.sizes.all())
            for size in sizes:
                if size.stock > 0:
                    available_stocks.append(size)
            product_size = available_stocks[0] if available_stocks else None
            products_data.append(
                {
                    "id": product.pk,
                    "title": product.title,
                    "price": product_size.price,
                    "slug": product.product_slug,
                    "discount_price": product_size.discount_price,
                    "image_url": product.image_optimized.url,
                    "product_image_url": product.image_optimized_two.url,
                }
            )
        return JsonResponse({"products": products_data}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)})


def about(request):
    return render(request, "about.html")


def privacy(request):
    return render(request, "privacy.html")


def store_locator(request):
    return render(request, "store-locator.html")


def terms_and_conditions(request):
    return render(request, "terms-and-conditions.html")


def faqs(request):
    return render(request, "faqs.html")


def search(request):
    search_term = request.GET.get("q", "").strip()
    products = Product.objects.filter(
        Q(title__icontains=search_term) | Q(content__icontains=search_term)
    ).filter(status=True).annotate(stock=Sum("sizes__stock")).filter(stock__gt=0)
    products_data = []

    for product in products:
        product_image = ProductImage.objects.filter(product=product).first()
        product_size = ProductSize.objects.filter(product=product).first()
        products_data.append(
            {
                "product": product,
                "product_image_url": product_image if product_image else None,
                "product_size": product_size,
            }
        )

    return render(
        request,
        "search.html",
        {
            "products": products,
            "products_data": products_data,
            "search_term": search_term,
        },
    )


@csrf_exempt
def apply_discount(request):
    if request.method == "POST":
        # Get the discount code from the request
        try:
            data = json.loads(request.body)
            discount_code = data.get("discount_code", "").strip()

            # Get the cart total from the session
            cart = request.session.get("cart", {})
            total = 0
            if cart:
                for item in cart.values():
                    sub_total = item["quantity"] * item["price"]
                    total += sub_total

            # Validate the discount code
            discount = Discount.objects.filter(
                code=discount_code, is_active=True
            ).first()

            if discount and discount.is_valid() and total >= discount.min_purchase:
                # Apply the discount (either percentage or fixed amount)
                if discount.discount_percent:
                    discount_amount = (total * discount.discount_percent) / 100
                elif discount.discount_amount:
                    discount_amount = discount.discount_amount
                else:
                    discount_amount = 0

                # Calculate the updated price
                updated_price = total - discount_amount + 75000
                snapppay_eligible = False
                snapppay_discount_title_message = ""
                snapppay_discount_description = ""
                try:
                    discount_jwt_token = get_snapppay_jwt_token()
                    if discount_jwt_token:
                        res = check_snapppay_eligibility_and_display(discount_jwt_token, updated_price)
                        snapppay_eligible = res["eligible"]
                        snapppay_discount_title_message = res["title_message"]
                        snapppay_discount_description = res["description"]
                except Exception as e:
                    snapppay_eligible = False
                    snapppay_discount_title_message = ""
                    snapppay_discount_description = ""
                    print(e)
                return JsonResponse({"success": True, "updated_price": updated_price, "snapppay_eligible": snapppay_eligible, "snapppay_discount_title_message": snapppay_discount_title_message, "snapppay_discount_description": snapppay_discount_description})

            return JsonResponse(
                {
                    "success": False,
                    "message": "کد تخفیف معتبر نیست یا شرایط استفاده از آن رعایت نشده است.",
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


def custom_404(request, exception):
    return render(request, "404.html", status=404)
