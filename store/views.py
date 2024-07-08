from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from .models import Product, Category


def home(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'home.html', context)


def about(request):
    return render(request, 'about.html')


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
            messages.success(request, 'You have registered successfully')
            return redirect('home')
        else:
            messages.success(request, 'Whoops! There was a problem Registering, please try again')
            return redirect('register')
    else:
        return render(request, 'register.html', context)
