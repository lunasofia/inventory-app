from django.contrib import admin

from .models import Bag, PackingItem, Template, TemplateItem, Trip, TripShare


class PackingItemInline(admin.TabularInline):
    model = PackingItem
    extra = 0


class BagInline(admin.TabularInline):
    model = Bag
    extra = 0


class TripShareInline(admin.TabularInline):
    model = TripShare
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'destination', 'status', 'start_date')
    list_filter = ('status', 'owner')
    search_fields = ('name', 'destination')
    inlines = [BagInline, PackingItemInline, TripShareInline]


class TemplateItemInline(admin.TabularInline):
    model = TemplateItem
    extra = 0


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    list_filter = ('owner',)
    search_fields = ('name',)
    inlines = [TemplateItemInline]
