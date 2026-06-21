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
    # Templates / reuse
    path('templates/', views.template_list, name='template_list'),
    path('trips/<int:pk>/save-template/', views.save_as_template, name='save_as_template'),
    path('trips/<int:pk>/diff/', views.template_diff, name='template_diff'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:pk>/items/add/', views.template_item_add, name='template_item_add'),
    path('templates/<int:pk>/items/<int:item_pk>/', views.template_item_row, name='template_item_row'),
    path('templates/<int:pk>/items/<int:item_pk>/edit/', views.template_item_edit, name='template_item_edit'),
    path('templates/<int:pk>/items/<int:item_pk>/delete/', views.template_item_delete, name='template_item_delete'),
]
