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
    path('trips/<int:pk>/items/<int:item_pk>/toggle/', views.item_toggle, name='item_toggle'),
    # Grouping lens + bags (HTMX)
    path('trips/<int:pk>/group/', views.set_group, name='set_group'),
    path('trips/<int:pk>/bags/add/', views.bag_create, name='bag_create'),
    path('trips/<int:pk>/bags/<int:bag_pk>/', views.bag_chip, name='bag_chip'),
    path('trips/<int:pk>/bags/<int:bag_pk>/edit/', views.bag_edit, name='bag_edit'),
    path('trips/<int:pk>/bags/<int:bag_pk>/delete/', views.bag_delete, name='bag_delete'),
    path('trips/<int:pk>/bags/<int:bag_pk>/mark/', views.bag_mark, name='bag_mark'),
    # Sharing (owner-only)
    path('trips/<int:pk>/share/add/', views.share_add, name='share_add'),
    path('trips/<int:pk>/share/suggest/', views.collaborator_suggest, name='collaborator_suggest'),
    path('trips/<int:pk>/share/<int:share_pk>/update/', views.share_update, name='share_update'),
    path('trips/<int:pk>/share/<int:share_pk>/revoke/', views.share_revoke, name='share_revoke'),
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
    # Category management
    path('categories/', views.category_manage, name='category_manage'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/', views.category_chip, name='category_chip'),
    path('categories/<int:pk>/rename/', views.category_rename, name='category_rename'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
