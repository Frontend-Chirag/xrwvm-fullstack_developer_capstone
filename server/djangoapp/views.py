from .models import CarMake, CarModel
from .populate import initiate
from .restapis import (
    analyze_review_sentiments,
    get_request,
    post_review,
)

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import logging


logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    """Authenticate a user."""
    data = json.loads(request.body)

    username = data["userName"]
    password = data["password"]

    user = authenticate(
        username=username,
        password=password,
    )

    response = {
        "userName": username,
    }

    if user is not None:
        login(request, user)
        response = {
            "userName": username,
            "status": "Authenticated",
        }

    return JsonResponse(response)


def logout_request(request):
    """Logout current user."""
    logout(request)

    return JsonResponse({
        "userName": "",
    })


@csrf_exempt
def registration(request):
    """Register a new user."""

    data = json.loads(request.body)

    username = data["userName"]
    password = data["password"]
    first_name = data["firstName"]
    last_name = data["lastName"]
    email = data["email"]

    username_exist = False

    try:
        User.objects.get(username=username)
        username_exist = True

    except User.DoesNotExist:
        logger.debug("%s is new user", username)

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email,
        )

        login(request, user)

        return JsonResponse({
            "userName": username,
            "status": "Authenticated",
        })

    return JsonResponse({
        "userName": username,
        "error": "Already Registered",
    })


def get_dealerships(request, state="All"):
    """Return dealerships."""

    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state

    dealerships = get_request(endpoint)

    return JsonResponse({
        "status": 200,
        "dealers": dealerships,
    })


def get_dealer_reviews(request, dealer_id):
    """Return reviews for a dealership."""

    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)

        reviews = get_request(endpoint)

        for review in reviews:
            sentiment = analyze_review_sentiments(
                review["review"]
            )

            if sentiment and "sentiment" in sentiment:
                review["sentiment"] = sentiment["sentiment"]
            else:
                review["sentiment"] = "neutral"

        return JsonResponse({
            "status": 200,
            "reviews": reviews,
        })

    return JsonResponse({
        "status": 400,
        "message": "Bad Request",
    })


def get_dealer_details(request, dealer_id):
    """Return dealership details."""

    if dealer_id:
        endpoint = "/fetchDealer/" + str(dealer_id)

        dealership = get_request(endpoint)

        return JsonResponse({
            "status": 200,
            "dealer": [dealership],
        })

    return JsonResponse({
        "status": 400,
        "message": "Bad Request",
    })


def add_review(request):
    """Add a review."""

    if not request.user.is_anonymous:
        data = json.loads(request.body)

        try:
            post_review(data)

            return JsonResponse({
                "status": 200,
            })

        except Exception as err:
            logger.error(err)

            return JsonResponse({
                "status": 401,
                "message": "Error in posting review",
            })

    return JsonResponse({
        "status": 403,
        "message": "Unauthorized",
    })


def get_cars(request):
    """Return all cars."""

    if CarMake.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related(
        "car_make"
    )

    cars = []

    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name,
        })

    return JsonResponse({
        "CarModels": cars,
    })
