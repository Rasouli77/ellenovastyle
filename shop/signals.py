from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product, Cart, OrderProduct, Order, ProductSize, ProductImage
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .utils import send_request_to_stock_management
import os


@receiver(post_save, sender=Product)
def soft_delete_cart(sender, instance, created, **kwargs):
    if not created:
        if instance.deleted:
            carts = Cart.objects.filter(product=instance)
            for cart in carts:
                cart.delete()


@receiver(post_save, sender=Product)
def soft_delete_order_product(sender, instance, created, **kwargs):
    if not created:
        if instance.deleted:
            order_products = OrderProduct.objects.filter(product=instance)
            for order_product in order_products:
                order_product.delete()


@receiver(post_save, sender=Order)
def soft_delete_order_product(sender, instance, created, **kwargs):
    if not created:
        if instance.deleted:
            order_products = OrderProduct.objects.filter(order=instance)
            for order_product in order_products:
                order_product.delete()


@receiver(pre_save, sender=Order)
def update_stock_on_status_change(sender, instance, **kwargs):
    if instance.pk:
        order = Order.objects.get(pk=instance.pk)
        if order.status != instance.status and instance.status == "DO":
            order_items = OrderProduct.objects.filter(order=instance)
            for item in order_items:
                product_size = item.size
                product_size.stock -= item.quantity
                product_size.save()

                if product_size.product_code:
                    send_request_to_stock_management(
                        product_size.product_code, product_size.stock
                    )


@receiver(post_save, sender=Product)
def generate_webp_images(sender, instance, created, **kwargs):

    if instance.image and not instance.image_optimized:
        image = Image.open(instance.image.path)
        buffer = BytesIO()
        image.save(buffer, "WEBP", quality=80, optimize=True)
        base_filename = os.path.splitext(os.path.basename(instance.image.path))[0]
        new_filename = f"{base_filename}_webp.webp"
        instance.image_optimized.save(
            new_filename, ContentFile(buffer.getvalue()), save=False
        )
        instance.save()

    if instance.images.exists() and not instance.image_optimized_two:
        image = Image.open(instance.images.all()[0].image.path)
        buffer = BytesIO()
        image.save(buffer, "WEBP", quality=80, optimize=True)
        file_basename = os.path.splitext(
            os.path.basename(instance.images.all()[0].image.path)
        )[0]
        new_filename = f"{file_basename}_webp.webp"
        instance.image_optimized_two.save(
            new_filename, ContentFile(buffer.getvalue()), save=False
        )
        instance.save()
