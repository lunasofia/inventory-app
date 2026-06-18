from django.contrib import admin

from .models import Category, Condition, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    list_filter = ('owner',)
    search_fields = ('name',)


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_default', 'sort_order')
    list_filter = ('owner', 'is_default')
    search_fields = ('name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'times_used')
    list_filter = ('owner', 'category')
    search_fields = ('name',)
