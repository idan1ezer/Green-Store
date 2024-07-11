from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from cart.cart import Cart
from .forms import SignUpForm, UserUpdateForm, ChangePasswordForm, UserInfoForm
from .models import Product, Category, Profile
import json


def home(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'home.html', context)


def about(request):
    return render(request, 'about.html')


def category_summary(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'category_summary.html', context)


def category(request, foo):
    foo = foo.replace('_', ' ')
    foo = foo.replace('-', ' ')

    try:
        # Look up the Category
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        context = {'category': category, 'products': products}
        return render(request, 'category.html', context)

    except:
        messages.error(request, 'Category does not exist')
        return redirect('home')


def product(request, pk):
    product = Product.objects.get(id=pk)
    context = {'product': product}
    return render(request, 'product.html', context)


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You are now logged in')

            # Do some shopping cart stuff
            current_user = Profile.objects.get(user__id=request.user.id)
            # Get their saved cart from database
            saved_cart = current_user.old_cart
            # Convert database string to python dictionary
            if saved_cart:
                converted_cart = json.loads(saved_cart)
                # Add the loaded cart dictionary to our session
                # Get the cart
                cart = Cart(request)
                # Loop through the cart and add the items from the database
                for key, value in converted_cart.items():
                    cart.add(product=key, quantity=value, is_load=True)

            return redirect('home')
        else:
            messages.success(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


def register_user(request):
    form = SignUpForm()
    context = {'form': form}
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            # log in user
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Username created - Please fill out your info belowcmd')
            return redirect('update_info')
        else:
            messages.success(request, 'Whoops! There was a problem Registering, please try again')
            return redirect('register')
    else:
        return render(request, 'register.html', context)


def update_user(request):
    if request.user.is_authenticated:
        # Get the logged-in user
        current_user = User.objects.get(id=request.user.id)
        form = UserUpdateForm(request.POST or None, instance=current_user)

        if form.is_valid():
            form.save()
            login(request, current_user)
            messages.success(request, 'Your account has been updated!')
            return redirect('home')
        else:
            context = {'form': form}
            return render(request, 'update_user.html', context)

    else:
        messages.error(request, 'You are not logged in')
        return redirect('login')


def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user
        # Did they fill out the form
        if request.method == 'POST':
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                login(request, current_user)
                messages.success(request, 'Your password has been updated!')
                return redirect('home')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                return redirect('update_password')
        else:
            form = ChangePasswordForm(current_user)
            context = {'form': form}
            return render(request, 'update_password.html', context)
    else:
        messages.error(request, 'You are not logged in')
        return redirect('login')


def update_info(request):
    if request.user.is_authenticated:
        # Get the logged-in user
        current_user = Profile.objects.get(user__id=request.user.id)
        form = UserInfoForm(request.POST or None, instance=current_user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your info has been updated!')
            return redirect('home')
        else:
            context = {'form': form}
            return render(request, 'update_info.html', context)

    else:
        messages.error(request, 'You are not logged in')
        return redirect('login')


def search(request):
    # Determine if they filled out the form
    if request.method == 'POST':
        searched = request.POST['searched']
        # Query the Product DB model
        searched = Product.objects.filter(
            Q(name__icontains=searched) |
            Q(description__icontains=searched)
        )
        # Test for null
        if not searched:
            messages.success(request, 'Product does not exist')
            return render(request, 'search.html', {})
        else:
            return render(request, 'search.html', {'searched': searched})
    else:
        return render(request, 'search.html', {})

