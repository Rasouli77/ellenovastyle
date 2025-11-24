from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core import settings
from .models import ProductSize


class UpdateProductSizeStock(APIView):
    def post(self, request, *args, **kwargs):

        api_key = request.headers.get("X-API-KEY")
        if api_key != settings.STOCK_API_KEY:
            return Response(
                {"error": "Forbidden Request"}, status=status.HTTP_403_FORBIDDEN
            )

        product_code = request.data.get("product_code")
        stock = request.data.get("stock")

        if not product_code or stock is None:
            return Response(
                {"error": "bad request"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product_size = ProductSize.objects.get(product_code=product_code)
            product_size.stock = stock
            product_size.save()
            return Response(
                {"success": "Updated Successfully"}, status=status.HTTP_200_OK
            )
        except ProductSize.DoesNotExist:
            return Response(
                {"error": "product not found"}, status=status.HTTP_404_NOT_FOUND
            )


class UpdateProductSizePrice(APIView):
    def post(self, request):
        if request.headers.get("Y-API-KEY") != settings.UPDATE_PRICE:
            return Response(
                {"error": "Forbidden Request"}, status=status.HTTP_403_FORBIDDEN
            )

        price = request.data.get("price")
        product_code = request.data.get("product_code")

        if not price:
            return Response(
                {"error": "Bad Request"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = ProductSize.objects.get(product_code=product_code)
            product.price = price
            product.save()
        except ProductSize.DoesNotExist:
            return Response(
                {"error": "Product Not Found"}, status=status.HTTP_404_NOT_FOUND
            )
