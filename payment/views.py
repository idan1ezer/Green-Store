from django.shortcuts import render, redirect
from django.contrib import messages

from cart.cart import Cart
from payment.forms import ShippingAddressForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from store.models import Profile

import datetime


def checkout(request):
    # Get the cart
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    totals = cart.get_totals()

    if request.user.is_authenticated:
        # Checkout as logged-in user
        # Shipping User
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        # Shipping form
        shipping_form = ShippingAddressForm(request.POST or None, instance=shipping_user)

        context = {'cart_products': cart_products, 'quantities': quantities, 'totals': totals,
                   'shipping_form': shipping_form}
        return render(request, 'payment/checkout.html', context)
    else:
        # Checkout as
        shipping_form = ShippingAddressForm(request.POST or None)
        context = {'cart_products': cart_products, 'quantities': quantities, 'totals': totals,
                   'shipping_form': shipping_form}
        return render(request, 'payment/checkout.html', context)


def payment_success(request):
    return render(request, 'payment/payment_success.html', {})


def billing_info(request):
    if request.POST:
        # Get the cart
        cart = Cart(request)
        cart_products = cart.get_products()
        quantities = cart.get_quantities()
        totals = cart.get_totals()

        # Create a session with Shipping Info
        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping

        billing_form = PaymentForm()
        shipping_info = request.POST
        context = {'cart_products': cart_products, 'quantities': quantities, 'totals': totals,
                   'shipping_info': shipping_info, 'billing_form': billing_form}
        return render(request, 'payment/billing_info.html', context)

        # Check to see if user is logged in
        # if request.user.is_authenticated:
        # Get the Billing Form
        # else:
        # Not logged in
        # pass

    else:
        messages.error(request, 'Access Denied!')
        return redirect('home')


def process_order(request):
    if request.POST:
        # Get the cart
        cart = Cart(request)
        cart_products = cart.get_products()
        quantities = cart.get_quantities()
        totals = cart.get_totals()

        # Get Billing Info from the last page
        payment_form = PaymentForm(request.POST or None)
        # Get Shipping Session Data
        my_shipping = request.session.get('my_shipping')

        # Gather Order Info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        # Create Shipping Address from session info
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals

        # Create an Order
        if request.user.is_authenticated:
            # logged in
            user = request.user
            # Create Order
            create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address,
                                 amount_paid=amount_paid)
            create_order.save()

            # Add Order Items
            create_order_items(user=user, order_id=create_order.pk, quantities=quantities, cart_products=cart_products)
            # Delete our cart
            for key in list(request.session.keys()):
                if key == 'session_key':
                    # Delete the key
                    del request.session[key]

            # Delete cart from database (old_cart field)
            current_user = Profile.objects.filter(user__id=request.user.id)
            # Delete shopping cart in database (old_cart field)
            current_user.update(old_cart="")

        else:
            # not logged in
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address,
                                 amount_paid=amount_paid)
            create_order.save()

            # Add Order Items
            create_order_items(user=None, order_id=create_order.pk, quantities=quantities, cart_products=cart_products)
            # Delete our cart
            for key in list(request.session.keys()):
                if key == 'session_key':
                    # Delete the key
                    del request.session[key]

        messages.success(request, 'Order Placed!')
        return redirect('home')

    else:
        messages.error(request, 'Access Denied!')
        return redirect('home')


def create_order_items(user, order_id, cart_products, quantities):
    # Add Order Items
    # Get product info
    for product in cart_products:
        # Get product ID
        product_id = product.id
        # Get product price
        if product.is_sale:
            price = product.sale_price
        else:
            price = product.price
        # Get product quantities
        for key, value in quantities.items():
            if int(key) == product_id:
                if user is not None:
                    create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user,
                                                  quantity=value, price=price)
                else:
                    create_order_item = OrderItem(order_id=order_id, product_id=product_id,
                                                  quantity=value, price=price)
                create_order_item.save()


def shipped_dashboard(request):
    if request.user.is_authenticated and request.user.is_superuser:
        my_orders = Order.objects.filter(shipped=True).order_by('-date_shipped')
        if request.POST:
            num = request.POST['num']
            update_shipping_status(request, num)
            messages.success(request, 'Shipping status has been updated!')

        return render(request, 'payment/shipped_dashboard.html', {'orders': my_orders})
    else:
        messages.error(request, 'Access Denied!')
        return redirect('home')


def not_shipped_dashboard(request):
    if request.user.is_authenticated and request.user.is_superuser:
        my_orders = Order.objects.filter(shipped=False).order_by('date_ordered')
        if request.POST:
            num = request.POST['num']
            update_shipping_status(request, num)
            messages.success(request, 'Shipping status has been updated!')

        return render(request, 'payment/not_shipped_dashboard.html', {'orders': my_orders})
    else:
        messages.error(request, 'Access Denied!')
        return redirect('home')


def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        # Get the Order
        order = Order.objects.get(id=pk)
        # Get the order items
        items = OrderItem.objects.filter(order__id=pk)

        if request.POST:
            update_shipping_status(request, pk)

            messages.success(request, 'Shipping status has been updated!')
            return redirect('home')

        context = {'order': order, 'items': items}
        return render(request, 'payment/orders.html', context)
    else:
        messages.error(request, 'Access Denied!')
        return redirect('home')


def update_shipping_status(request, pk):
    status = request.POST.get('shipping_status')

    # two ways to update current obj
    # 1. MODEL.objects.get(id=pk) -> MODEL.FIELD = NEW_VALUE -> MODEL.save()
    # 2. MODEL.objects.filter(id=pk) -> MODEL.update(FIELD = NEW VALUE)
    if status == "true":
        order = Order.objects.get(id=pk)
        order.shipped = True
        order.date_shipped = datetime.datetime.now()
        order.save()
    else:
        order = Order.objects.filter(id=pk)
        order.update(shipped=False)
