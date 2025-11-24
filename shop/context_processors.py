from .models import Product, ProductSize, Category


def cart(request):
    cart = request.session.get("cart", {})
    all_quantity = 0
    all_total = 0
    shipping_and_all_total = 0
    cart_key = 0
    enriched_cart = []

    # Process the cart
    for key, item in cart.items():
        product = Product.objects.filter(id=item["product_id"]).first()
        product_size = ProductSize.objects.filter(id=item["size_id"]).first()
        product_id = item["product_id"]
        size_id = item["size_id"]
        cart_key = f"{product_id}-{size_id}"

        if product and product_size:
            total_price = (
                item["quantity"] * item["price"]
            )  # Calculate total price for this item
            enriched_cart.append(
                {
                    "product": product,  # Product object
                    "size": product_size,  # ProductSize object
                    "quantity": item["quantity"],  # Quantity of this size
                    "price": item["price"],  # Price per unit
                    "discount_price": item["discount_price"],  # Discount price (if any)
                    "total": total_price,  # Total price for this line item
                }
            )
            all_total += total_price  # Update the overall total
            all_quantity += item["quantity"]  # Update the overall quantity

    # Add shipping cost to the total
    shipping_and_all_total = 75000 + all_total

    return {
        "cart": enriched_cart,  # Enriched cart data
        "all_total": all_total,  # Total cost of items
        "all_quantity": all_quantity,  # Total quantity of items
        "shipping_and_all_total": shipping_and_all_total,  # Total with shipping
        "cart_key": cart_key,
    }


def category(request):
    categories = Category.objects.defer("content", "seo_title", "meta").all()
    return {"categories": categories}
