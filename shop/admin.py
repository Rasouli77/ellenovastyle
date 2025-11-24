from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from .models import (
    Category,
    Product,
    Cart,
    PaymentLog,
    Order,
    OrderProduct,
    Attribute,
    AttributeValue,
    ProductAttributeValue,
    ProductImage,
    ProductSize,
    Discount,
)
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from admin_confirm import AdminConfirmMixin, confirm_action
import jdatetime



class HasImage(admin.SimpleListFilter):
    title = "تصویر"
    parameter_name = "picture"

    def lookups(self, request, model_admin):
        return [
            ("has_main_picture", "با تصویر اصلی"),
            ("without_main_picture", "بدون تصویر اصلی"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "has_main_picture":
            return queryset.exclude(image="")

        if self.value() == "without_main_picture":
            return queryset.filter(image="")
            
            
class HasSnapppayTransactionId(admin.SimpleListFilter):
    title = "کد تراکنش اسنپ پی"
    parameter_name = "snapppay_transaction_id"
    
    def lookups(self, request, model_admin):
        return [
                ("has_snapppay_transaction_id", "دارد"),
                ("has_no_snapppay_transaction_id", "ندارد"),
            ]
            
    def queryset(self, request, queryset):
        if self.value() == "has_snapppay_transaction_id":
            return queryset.exclude(snapppay_transaction_id__isnull=True)
            
        if self.value() == "has_no_snapppay_transaction_id":
            return queryset.filter(snapppay_transaction_id__isnull=True)

class NoSEOContent(admin.SimpleListFilter):
    title = "محتوای سئو"
    parameter_name = "noproductcontent"

    def lookups(self, request, model_admin):
        return [
            ("with_seo_content", "با محتوای سئو"),
            ("without_seo_content", "بدون محتوای سئو"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "with_seo_content":
            return queryset.exclude(content="")
        if self.value() == "without_seo_content":
            return queryset.filter(content="")


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = (
            "title",
            "seo_title",
            "meta",
            "product_slug",
            "content",
            "status",
            "category",
            "content_code",
            "glass",
            "frame",
            "color",
        )


class ProductSizeResource(resources.ModelResource):
    class Meta:
        model = ProductSize
        fields = (
            "product",
            "width",
            "height",
            "product_code",
            "price",
            "stock",
            "discount_percent",
        )


# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):

    def delete_queryset(self, request, queryset):
        for item in queryset:
            item.delete()

    class Meta:
        abstract = True


class ProductSizeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = [
        "product",
        "product_code",
        "height",
        "width",
        "stock",
        "price",
        "discount_percent",
        "discount_price",
    ]
    search_fields = ["product_code", "product__title"]
    list_editable = ["stock"]


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0


class ProductOrderInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ["picture", "price", "width", "height", "current_price", "order_item_discount"]
    search_fields = ["size"]
    autocomplete_fields = ["size"]
    fields = ["picture", "product", "size", "width", "height", "current_price", "quantity", "price", "order_item_discount"]
    def width(self, obj):
        width = obj.size.width
        return format_html("<span>{}</span>", width)
    width.short_description = "عرض"
    def height(self, obj):
        height = obj.size.height
        return format_html("<span>{}</span>", height)
    height.short_description = "طول"
    def current_price(self, obj):
        price = obj.size.price
        return format_html("<span>{}</span>", price)
    current_price.short_description = "قیمت فعلی"
    def picture(self, obj):
        if obj.product and obj.product.image_optimized:
            pic_link = obj.product.image_optimized.url
            return format_html("<img src='{}' style='height: 80px; max-width: 120px;'>", pic_link)
        else:
            return format_html("<span>فاقد تصویر</span>")
    picture.short_description = "تصویر"

class CategoryAdmin(BaseModelAdmin):
    list_display = ["id", "__str__"]


class ProductImageAdmin(BaseModelAdmin):
    pass


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [ProductImageInline, ProductSizeInline]
    exclude = ["date_created"]
    list_editable = ["status"]
    list_display = [
        "image_thumbnail",
        "id",
        "title",
        "category",
        "content_code",
        "glass",
        "frame",
        "color",
        "status",
    ]
    list_filter = [
        "date_created",
        HasImage,
        "category",
        "status",
        "frame",
        "glass",
        "color",
        NoSEOContent,
    ]
    search_fields = ["title", "content_code"]

    def image_thumbnail(self, obj):
        if obj.image:
            return mark_safe(f'<img src={obj.image.url} width="100" height="100"/>')
        else:
            return "فاقد تصویر"

    image_thumbnail.short_description = "تصویر"


class CartAdmin(BaseModelAdmin):
    pass


class OrderAdmin(AdminConfirmMixin, BaseModelAdmin):
    inlines = [ProductOrderInline]
    exclude = ["date_created"]
    list_display = [
        "__str__",
        "status_colored",
        "order_mobile",
        "order_name",
        "order_city",
        "total_price",
        "status",
        "payment_method",
        "date_created_persian",
        "date_modified_persian",
    ]
    actions = ["snapppay_payment_cancel_action", "snapppay_payment_update_action"]

    def status_colored(self, obj):
        if obj.status == "FA":
            return format_html("<span>❌</span>")
        if obj.status == "DO":
            return format_html("<span>✅</span>")
        if obj.status == "SC":
            return format_html("<span>❌</span>")
        if obj.status == "SU":
            return format_html("<span>🔄</span>")
        if obj.status == "ZC":
            return format_html("<span>❌</span>")

    status_colored.short_description = "وضعیت"

    def date_created_persian(self, obj):
        persian_date = jdatetime.datetime.fromgregorian(datetime=obj.date_created)
        return persian_date.strftime("%B %d، ساعت %H:%M")

    date_created_persian.short_description = "تاریخ ایجاد"

    def date_modified_persian(self, obj):
        persian_date = jdatetime.datetime.fromgregorian(datetime=obj.modified_date)
        return persian_date.strftime("%B %d، ساعت %H:%M")

    date_modified_persian.short_description = "تاریخ تغییر"

    list_filter = ["date_created", "status", "payment_method", "modified_date", HasSnapppayTransactionId]
    exclude = ["order_user_name", "user", "date_created"]
    readonly_fields = [
        "order_name",
        "order_mobile",
        "order_address",
        "payment_method",
        "status",
        "total_price",
        "order_discount",
        "order_discount_code",
        "gateway_bank_order_authority",
        "gateway_bank_order_ref_id",
        "snapppay_payment_token",
        "snapppay_transaction_id",
    ]
    search_fields = ["order_mobile", "id", "snapppay_transaction_id", "order_name"]
    @confirm_action
    def snapppay_payment_cancel_action(self, request, queryset):
        if queryset.count() != 1:
            messages.warning(request, "فقط یک مورد انتخاب کنید")
            return

        order = queryset.first()

        if order.payment_method != "snapppay":
            messages.error(request, "روش پرداخت این سفارش اسنپ پی نیست")

        if order.snapppay_payment_token and order.snapppay_transaction_id:
            url = reverse("snapppay_cancel", args=[order.snapppay_payment_token])
            return redirect(url)
        else:
            messages.error(request, "این سفارش توکن اسنپ پی ندارد")
            return

    snapppay_payment_cancel_action.short_description = "لغو سفارش اسنپ پی"
    @confirm_action
    def snapppay_payment_update_action(self, request, queryset):
        if queryset.count() != 1:
            messages.warning(request, "فقط یک مورد انتخاب کنید")
            return

        order = queryset.first()

        if order.payment_method != "snapppay":
            messages.error(request, "روش پرداخت این سفارش اسنپ پی نیست")

        if order.snapppay_payment_token and order.snapppay_transaction_id:
            url = reverse("snapppay_update", args=[order.pk])
            return redirect(url)
        else:
            messages.error(request, "این سفارش توکن اسنپ پی ندارد")
            return

    snapppay_payment_update_action.short_description = "آپدیت سفارش اسنپ پی"

class PaymentLogAdmin(BaseModelAdmin):
    pass


class OrderProductAdmin(BaseModelAdmin):
    list_display = ["order", "product", "size", "quantity", "price"]
    readonly_fields = ["price", "size", "order_item_discount"]


class AttributeAdmin(admin.ModelAdmin):
    pass


class AttributeValueAdmin(admin.ModelAdmin):
    pass


class ProductAttributeValueAdmin(admin.ModelAdmin):
    pass


class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "min_purchase",
        "discount_percent",
        "discount_amount",
        "is_active",
    ]
    list_filter = ["is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "code"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductImage)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(PaymentLog, PaymentLogAdmin)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(ProductSize, ProductSizeAdmin)
admin.site.register(Discount, DiscountAdmin)
