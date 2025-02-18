from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from .models import CarModel
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')


# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/ibm-course-137_ibm-course-137/dealership-package/get-dealership.json"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        print(dealerships)
        context['dealerships'] = dealerships
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = "https://eu-de.functions.appdomain.cloud/api/v1/web/ibm-course-137_ibm-course-137/dealership-package/get-review.json"
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        print(reviews)

        context['reviews'] = reviews
        context['dealer_id'] = dealer_id
        dealerships = get_dealers_from_cf("https://eu-de.functions.appdomain.cloud/api/v1/web/ibm-course-137_ibm-course-137/dealership-package/get-dealership.json")
        dealer = [d for d in dealerships if d.id == dealer_id]
        context['dealer_name'] = dealer[0].full_name
    return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    if request.method == "GET":
        context = {}
        cars_all = CarModel.objects.all()
        cars = [c for c in cars_all if c.dealerId == dealer_id]
        context["cars"] = cars
        context["dealer_id"] = dealer_id
        dealerships = get_dealers_from_cf("https://eu-de.functions.appdomain.cloud/api/v1/web/ibm-course-137_ibm-course-137/dealership-package/get-dealership.json")
        dealer = [d for d in dealerships if d.id == dealer_id]
        context['dealer_name'] = dealer[0].full_name
        return render(request, 'djangoapp/add_review.html', context)
    if request.method == "POST":
        if request.user.is_authenticated:
            url = "https://eu-de.functions.appdomain.cloud/api/v1/web/ibm-course-137_ibm-course-137/dealership-package/post-review.json"
            review = {}
            review['name'] = request.user.first_name + " " + request.user.last_name
            review['dealership'] = dealer_id
            review['review'] = request.POST['content']
            try:
                request.POST["purchasecheck"]
                review['purchase'] = True
            except:
                review["purchase"] = False
            review['purchase_date'] = request.POST['purchasedate']
            car = CarModel.objects.get(id = request.POST['car'])
            if car:
                review['car_make'] = car.make.name
                review['car_model'] = car.name
                review['car_year'] = car.year.strftime("%Y")
            json_payload = {}
            json_payload["review"] = review
            response = post_request(url, payload=json_payload)
    return redirect('djangoapp:dealer_details', dealer_id = dealer_id)

