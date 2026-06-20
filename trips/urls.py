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
    # Grouping lens + bags (HTMX)
    path('trips/<int:pk>/group/', views.set_group, name='set_group'),
    path('trips/<int:pk>/bags/add/', views.bag_create, name='bag_create'),
    path('trips/<int:pk>/bags/<int:bag_pk>/', views.bag_chip, name='bag_chip'),
    path('trips/<int:pk>/bags/<int:bag_pk>/edit/', views.bag_edit, name='bag_edit'),
    path('trips/<int:pk>/bags/<int:bag_pk>/delete/', views.bag_delete, name='bag_delete'),
    path('trips/<int:pk>/bags/<int:bag_pk>/mark/', views.bag_mark, name='bag_mark'),
    # Check-off packing mode (HTMX)
    path('trips/<int:pk>/pack/', views.packing_mode, name='packing_mode'),
    path('trips/<int:pk>/pack/group/', views.pack_group, name='pack_group'),
    path('trips/<int:pk>/pack/<int:item_pk>/toggle/', views.pack_toggle, name='pack_toggle'),
    path('trips/<int:pk>/pack/bags/<int:bag_pk>/mark/', views.pack_bag_mark, name='pack_bag_mark'),
]
