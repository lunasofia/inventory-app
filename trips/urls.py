from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('trips/new/', views.trip_create, name='trip_create'),
    path('trips/<int:pk>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:pk>/edit/', views.trip_edit, name='trip_edit'),
    path('trips/<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    # Packing-list items (HTMX)
    path('trips/<int:pk>/items/add/', views.item_add, name='item_add'),
    path('trips/<int:pk>/items/suggest/', views.item_suggest, name='item_suggest'),
    path('trips/<int:pk>/items/<int:item_pk>/', views.item_row, name='item_row'),
    path('trips/<int:pk>/items/<int:item_pk>/edit/', views.item_edit, name='item_edit'),
    path('trips/<int:pk>/items/<int:item_pk>/delete/', views.item_delete, name='item_delete'),
]
