from django.contrib import admin
from django.urls import path, include
from shop import views
from django.conf import settings
from django.conf.urls.static import static
from custom_login.views import edit_user
from django.contrib.auth import views as auth_views
from blog.views import blog, blog_details, blog_search
from django.conf.urls import handler404
from django.views.static import serve
from shop.api_views import UpdateProductSizeStock, UpdateProductSizePrice
from shop.sitemaps import StaticCategorySitemap, ProductSitemap
from django.contrib.sitemaps.views import sitemap

sitemaps = {"products": ProductSitemap, "categories": StaticCategorySitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("checkout/", views.checkout, name="checkout"),
    path("bank-gateway/<int:order_id>", views.bank_gateway, name="bank-gateway"),
    path(
        "snapppay-gateway/<int:order_id>",
        views.snapppay_gateway,
        name="snapppay_gateway",
    ),
    path("", views.index, name="index"),
    path("category/<str:title>/", views.store, name="store"),
    path("product/<str:product_slug>/", views.product, name="product"),
    path("user/", include("custom_login.urls")),
    path("add_to_cart", views.add_to_cart, name="add_to_cart"),
    path("cart", views.cart_detail, name="cart"),
    path(
        "cart/remove/<str:cart_key>/", views.remove_from_cart, name="remove_from_cart"
    ),
    path("profile/edit/<int:user_id>/", views.edit, name="edit_profile"),
    path("profile/orders/<int:user_id>/", views.profile_orders, name="profile_orders"),
    path("profile/dashboard", views.profile_panel, name="profile_panel"),
    path("edit/<int:user_id>/", edit_user, name="edit_user"),
    path(
        "load/load_more_products/", views.load_more_products, name="load_more_products"
    ),
    path("about-us/", views.about, name="about-us"),
    path("privacy/", views.privacy, name="privacy"),
    path("store-locator", views.store_locator, name="store-locator"),
    path(
        "terms-and-conditions", views.terms_and_conditions, name="terms-and-conditions"
    ),
    path("faqs", views.faqs, name="faqs"),
    path("verify", views.verify, name="verify"),
    path("snapppay-result", views.snapppay_payment_result, name="snapppay_result"),
    path("snapppay-verify", views.snapppay_payment_verify, name="snapppay_verify"),
    path("snapppay-cancel/<str:snapppay_payment_token>", views.snapppay_payment_cancel, name="snapppay_cancel"),
    path("snapppay-update/<int:order_id>", views.snapppay_payment_update, name="snapppay_update"),
    path("search", views.search, name="search"),
    path("tinymce/", include("tinymce.urls")),
    path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
    path("blog", blog, name="blog"),
    path("blog/search", blog_search, name="blog_search"),
    path("blog/<str:slug>", blog_details, name="blog_details"),
    path("apply-discount/", views.apply_discount, name="apply_discount"),
    path("api/update-stock/", UpdateProductSizeStock.as_view(), name="update-stock"),
    path("api/update-price/", UpdateProductSizePrice.as_view(), name="update-price"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

handler404 = "shop.views.custom_404"

# This serves media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)