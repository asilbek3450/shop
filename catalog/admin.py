from django.contrib import admin

from .models import Category, Product, ProductLike, Review, Wishlist


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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_reply", "is_hidden", "created_at")
    list_filter = ("rating", "is_hidden")
    search_fields = ("product__name", "user__phone", "body")
    autocomplete_fields = ("product", "user", "parent")

    @admin.display(boolean=True, description="Reply?")
    def is_reply(self, obj):
        return obj.parent_id is not None


@admin.register(ProductLike)
class ProductLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    autocomplete_fields = ("user", "product")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    autocomplete_fields = ("user", "product")
