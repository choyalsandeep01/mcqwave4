
from django.contrib import admin
from django.urls import path, include
from home.views import home_view
from home.views import logout_view
urlpatterns = [
    path('', home_view,  name='home' ),
    path('logout/', logout_view, name='logout'),
]

