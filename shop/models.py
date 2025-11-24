from typing import Any
from django.db import models
from django.contrib.auth.models import User
from core.settings import AUTH_USER_MODEL
from custom_login.models import City
from tinymce.models import HTMLField
from django.utils import timezone
from datetime import datetime


# Create your models here.


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class BaseModel(models.Model):
    deleted = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = BaseModelManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.save()


class Category(BaseModel):
    title = models.CharField(max_length=100, verbose_name="عنوان")
    persian_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="نام فارسی")
    seo_title = models.CharField(max_length=255, verbose_name="عنوان سئو", null=True)
    meta = models.CharField(max_length=255, verbose_name="توضیحات سئو", null=True)
    content = HTMLField(null=True, verbose_name="محتوای سئو")
    image = models.ImageField(
        upload_to="image/product", null=True, blank=True, verbose_name="تصویر دسته بندی"
    )

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی"

    def __str__(self):
        return self.title


class Product(BaseModel):
    Glasses = [("با شیشه", "با شیشه"), ("بدون شیشه", "بدون شیشه")]
    Frames = [
        ("تخت 2 در 2", "تخت 2 در 2"),
        ("تخت 2 در 3", "تخت 2 در 3"),
        ("هرمی 2", "هرمی 2"),
        ("هرمی 3", "هرمی 3"),
        ("فلز", "فلز"),
        ("گرد 1 در 1", "گرد 1 در 1"),
        ("تخت 3 در 3", "تخت 3 در 3"),
        ("عمیق 2.5 در 4.5", "عمیق 2.5 در 4.5"),
        ("تخت 3 در 2", "تخت 3 در 2"),
        ("قوس دار 3.5 در 2", "قوس دار 3.5 در 2"),
        ("قوس دار 4.5 در 3.5", "قوس دار 4.5 در 3.5"),
        ("تخت 5 در 2", "تخت 5 در 2"),
        ("معلق 5 در 4", "معلق 5 در 4"),
        ("تخت 4 در 2", "تخت 4 در 2"),
        ("عمیق 4 در 4", "عمیق 4 در 4"),
        ("طرحدار 7 در 4", "طرحدار 7 در 4"),
        ("تخت 1 در 2", "تخت 1 در 2"),
        ("قوس دار با حاشیه 4 در 2.5", "قوس دار با حاشیه 4 در 2.5"),
    ]
    Colors = [
        ("سفید", "سفید"),
        ("مشکی", "مشکی"),
        ("چوبی", "چوبی"),
        ("آبی", "آبی"),
        ("قرمز", "قرمز"),
        ("نارنجی", "نارنجی"),
        ("خاکستری", "خاکستری"),
        ("سبز", "سبز"),
    ]
    title = models.CharField(max_length=100, unique=True, verbose_name="عنوان")
    seo_title = models.CharField(
        max_length=255, verbose_name="عنوان سئو", null=True, blank=True
    )
    meta = models.CharField(
        max_length=255, verbose_name="توضیحات سئو", null=True, blank=True
    )
    product_slug = models.SlugField(null=True, verbose_name="لینک", blank=True)
    content = HTMLField(verbose_name="محتوای سئو", null=True, blank=True)
    image = models.ImageField(
        upload_to="image/product", null=True, blank=True, verbose_name="تصویر اصلی"
    )
    image_optimized = models.ImageField(
        upload_to="image/product", null=True, blank=True, verbose_name="تصویر لیست"
    )
    image_optimized_two = models.ImageField(
        upload_to="image/product", null=True, blank=True, verbose_name="تصویر دوم لیست"
    )
    status = models.BooleanField(
        default=True, verbose_name="وضعیت نمایش", db_index=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="دسته بندی",
        db_index=True,
    )
    content_code = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="کد محتوا", db_index=True
    )
    glass = models.CharField(
        max_length=255, choices=Glasses, null=True, blank=True, verbose_name="شیشه"
    )
    frame = models.CharField(max_length=255, choices=Frames, null=True, blank=True)
    color = models.CharField(max_length=255, choices=Colors, null=True, blank=True)
    date_created = models.DateTimeField(
        default=timezone.now, verbose_name="تاریخ ساخت", null=True, blank=True
    )
    modified_date = models.DateTimeField(
        auto_now=True, verbose_name="تاریخ تغییر", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            code = self.content_code[:3] + self.content_code[5:]
            base_title = "تابلو " + self.title + " کد " + code
            self.title = base_title
            n = 1

            while self.__class__.objects.filter(title=self.title).exists():
                self.title = f"{base_title}{n}"
                n += 1

        if self.product_slug is None:
            title = self.title
            slug_title = title.replace("تابلو ", "").replace(" کد ", "")
            slug_title_final = slug_title.replace(" ", "_")
            content_code = self.content_code
            self.product_slug = slug_title_final

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصول"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["content_code"]),
        ]

    def get_absolute_url(self):
        return f"/product/{self.product_slug}/"


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول",
        db_index=True,
    )
    image = models.ImageField(
        upload_to="image/product", null=True, blank=True, verbose_name="تصویر گالری"
    )

    def __str__(self):
        return self.product.title

    class Meta:
        verbose_name = "تصویر گالری محصول"
        verbose_name_plural = "تصویر گالری محصول"


class Attribute(BaseModel):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="دسته بندی"
    )
    name = models.CharField(max_length=255, verbose_name="عنوان مشخصه")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "مشخصه"
        verbose_name_plural = "مشخصه"


class AttributeValue(BaseModel):
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name="مشخصه"
    )
    value = models.CharField(max_length=255, verbose_name="ارزش مشخصه")

    class Meta:
        verbose_name = "ارزش مشخصه"
        verbose_name_plural = "ارزش مشخصه"

    def __str__(self):
        return f"{self.value}"


class ProductAttributeValue(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="محصول", db_index=True
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name="مشخصه", db_index=True
    )
    value = models.ForeignKey(
        AttributeValue, on_delete=models.CASCADE, verbose_name="ارزش", db_index=True
    )

    def __str__(self):
        return f"{self.attribute}: {self.value}"

    class Meta:
        verbose_name = "مشخصه های فنی محصولات"
        verbose_name_plural = "مشخصه های فنی محصولات"


class ProductSize(BaseModel):
    product = models.ForeignKey(
        Product, related_name="sizes", on_delete=models.CASCADE, verbose_name="محصول"
    )
    width = models.CharField(max_length=255, verbose_name="عرض")
    height = models.CharField(max_length=255, verbose_name="طول")
    product_code = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="کد محصول"
    )
    price = models.PositiveIntegerField(verbose_name="قیمت")
    stock = models.PositiveIntegerField(null=True)
    discount_percent = models.PositiveIntegerField(null=True, blank=True)
    discount_price = models.PositiveIntegerField(
        verbose_name="قیمت تخفیف", null=True, blank=True
    )

    class Meta:
        verbose_name = "محصول به تفکیک ابعاد"
        verbose_name_plural = "محصول به تفکیک ابعاد"

    def __str__(self):
        return f"{self.width, self.height, self.price}"

    def save(self):
        if self.discount_percent or self.discount_percent == 0:
            self.discount_price = int(self.price) * (
                (100 - self.discount_percent) / 100
            )
        else:
            self.discount_price = None
        return super().save()


class Cart(BaseModel):
    quantity = models.PositiveBigIntegerField(verbose_name="تعداد")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="محصول")
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر"
    )

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبد خرید"


class Order(BaseModel):
    total_price = models.IntegerField(verbose_name="مبغ کل")
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر"
    )
    STATUS_ITEMS = [
        ("FA", "پرداخت ناموفق"),
        ("DO", "پرداخت موفق"),
        ("SC", "پرداخت کنسل شده اسنپ پی"),
        ("SU", "سفارش آپدیت شده اسنپ پی"),
        ("ZC", "سفارش کنسل شده زرین پال"),
    ]
    status = models.CharField(
        max_length=5, null=True, blank=True, choices=STATUS_ITEMS, verbose_name="وضعیت"
    )
    order_user_name = models.CharField(
        max_length=200, null=True, verbose_name="نام"
    )  # remove null in production
    order_mobile = models.CharField(
        max_length=11, null=True, verbose_name="شماره موبایل"
    )  # remove null in production
    order_address = models.TextField(
        max_length=500, null=True, verbose_name="آدرس محل سکونت"
    )  # remove null in production
    order_city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, verbose_name="شهر"
    )  # remove null in production
    order_name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="نام"
    )
    gateway_bank_order_authority = models.CharField(max_length=50, null=True, verbose_name="کد مرجع زرین پال")
    gateway_bank_order_ref_id = models.BigIntegerField(null=True, verbose_name="کد رهگیری زرین پال")
    snapppay_payment_token = models.CharField(max_length=200, null=True, blank=True, verbose_name="توکن پرداخت اسنپ پی")
    snapppay_transaction_id = models.CharField(max_length=200, null=True, blank=True, verbose_name="کد تراکنش اسنپ پی")
    payment_method = models.CharField(
        max_length=20,
        choices=[("snapppay", "SnappPay"), ("zarinpal", "Zarinpal")],
        default="zarinpal",
        verbose_name="روش پرداخت",
    )
    order_discount = models.CharField(max_length=255, null=True, blank=True, verbose_name="مجموع کسری کد تخفیف")
    order_discount_code = models.CharField(max_length=255, null=True, blank=True, verbose_name="کدتخفیف سفارش")
    date_created = models.DateTimeField(
        default=timezone.now, verbose_name="تاریخ ساخت", null=True, blank=True
    )
    modified_date = models.DateTimeField(
        auto_now=True, verbose_name="تاریخ تغییر", null=True, blank=True
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"


class OrderProduct(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, verbose_name="سفارش", null=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="محصول")
    size = models.ForeignKey(
        ProductSize, on_delete=models.CASCADE, verbose_name="سایز", null=True
    )
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    price = models.IntegerField(verbose_name="قیمت")
    order_item_discount = models.CharField(max_length=255, null=True, blank=True, verbose_name="کسری کد تخفیف")

    def __str__(self):
        return str(self.pk)
        
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                original = OrderProduct.objects.get(pk=self.pk)
                if self.quantity < original.quantity:
                    try:
                        factor = self.quantity / original.quantity
                        order_item_discount_value = int(self.order_item_discount) * factor
                        self.order_item_discount = int(order_item_discount_value)
                    except Exception:
                        pass
            except Exception:
                pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "آیتم سفارشات"
        verbose_name_plural = "آیتم سفارشات"


class PaymentLog(models.Model):
    amount = models.IntegerField(verbose_name="مبلغ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ساخت")
    modified_date = models.DateTimeField(auto_now=True, verbose_name="تاریخ تغییر")
    user_id = models.PositiveIntegerField(verbose_name="کاربر")
    order_id = models.PositiveIntegerField(verbose_name="شماره سفارش")
    status = models.CharField(max_length=100, verbose_name="وضعیت")
    error_code = models.CharField(max_length=200, verbose_name="کد خطا")

    class Meta:
        verbose_name = "گزارش پرداختی"
        verbose_name_plural = "گزارش پرداختی"


class Discount(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام")
    code = models.CharField(max_length=255, verbose_name="کد تخفیف")
    valid_from = models.DateTimeField(verbose_name="تاریخ شروع")
    valid_to = models.DateTimeField(verbose_name="تاریخ پایان")
    min_purchase = models.PositiveIntegerField(verbose_name="حداقل مبلغ کل فاکتور")
    discount_percent = models.PositiveIntegerField(
        verbose_name="درصد تخفیف", null=True, blank=True
    )
    discount_amount = models.PositiveIntegerField(
        verbose_name="مبلغ تخفیف", null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کد تخفیف"

    def __str__(self):
        return self.code

    def is_valid(self):
        return self.is_active
