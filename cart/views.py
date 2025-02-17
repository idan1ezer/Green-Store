from django.shortcuts import render, get_object_or_404
from .cart import Cart
from store.models import Product
from django.http import JsonResponse
from django.contrib import messages


def cart_summary(request):
    # Get the cart
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    totals = cart.get_totals()

    context = {'cart_products': cart_products, 'quantities': quantities, 'totals': totals}
    return render(request, "cart_summary.html", context)


def add_to_cart(request):
    # Get the cart
    cart = Cart(request)
    # Test for POST
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        # Lookup product in DB
        product = get_object_or_404(Product, id=product_id)

        # Save to session
        cart.add(product=product, quantity=product_qty, is_load=False)

        # Get Cart Quantity
        cart_quantity = cart.__len__()

        # Return response
        # response = JsonResponse({'product_name': product.name})
        response = JsonResponse({'qty': cart_quantity})
        messages.success(request, "Product Added To Cart...")
        return response


def remove_from_cart(request):
    pass


def delete_cart(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        # Call delete function in Cart
        cart.delete(product=product_id)

        response = JsonResponse({'product': product_id})
        messages.success(request, "Product has been removed from Cart...")
        return response


def update_cart(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        cart.update(product=product_id, quantity=product_qty)

        response = JsonResponse({'qty': product_qty})
        messages.success(request, "Product Updated To Cart...")
        return response

