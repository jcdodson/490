from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_item, name='search_item'),
    path('price_graph/<int:item_id>/', views.price_graph, name='price_graph'),
]
