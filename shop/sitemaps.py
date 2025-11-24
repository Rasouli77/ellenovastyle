from django.contrib.sitemaps import Sitemap
from .models import Product


class StaticCategorySitemap(Sitemap):
    priority = 1

    changefreq = "weekly"

    def items(self):
        return [
            "/category/game/",
            "/category/anime-and-manga/",
            "/category/tv-shows/",
            "/category/music/",
        ]

    def location(self, item):
        return item


class ProductSitemap(Sitemap):
    priority = 1

    changefreq = "weekly"

    def items(self):
        return Product.objects.filter(status=True)

    def location(self, obj):
        return obj.get_absolute_url()
