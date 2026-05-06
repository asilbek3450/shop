from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "emoji", "sort_order", "is_active", "updated_at")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    ordering = ("sort_order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "subcategory", "price", "stock", "is_featured", "is_active")
    list_filter = ("category", "subcategory", "is_featured", "is_active", "badge")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "brand", "subcategory", "short_description", "description")
    autocomplete_fields = ("category",)
    list_editable = ("price", "stock", "is_featured", "is_active")
