from django.contrib import admin
from django.urls import path, include
from hive.views import hive_home,send_connection_request,handle_connection_request,share_bookmark,share_test,shared
urlpatterns = [
    path('', hive_home,  name='hive_home' ),
    path('connect/', send_connection_request, name='send_connection_request'),
    path('handle-connection-request/', handle_connection_request, name='handle_connection_request'),
    path('share-bookmark/<str:bookmark_id>/', share_bookmark, name='share_bookmark'),
    path('share-test/<str:test_id>/', share_test, name='share_test'),
    path('shared/<str:userId>/', shared, name='shared'),

]
