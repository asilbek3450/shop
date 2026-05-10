from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    emoji = models.CharField(max_length=8, default="🛍")
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    BADGE_BESTSELLER = "Bestseller"
    BADGE_NEW = "Yangi"
    BADGE_DISCOUNT = "Chegirma"
    BADGE_TOP = "Top"
    BADGE_CHOICES = [
        (BADGE_BESTSELLER, "Bestseller"),
        (BADGE_NEW, "Yangi"),
        (BADGE_DISCOUNT, "Chegirma"),
        (BADGE_TOP, "Top"),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    subcategory = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=120)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    price = models.PositiveIntegerField(help_text="Price in UZS")
    old_price = models.PositiveIntegerField(null=True, blank=True, help_text="Old price in UZS")
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=4.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    reviews_count = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=20, blank=True, choices=BADGE_CHOICES)
    image_key = models.CharField(max_length=120, default="electronics-airpods")
    colors = models.JSONField(default=list, blank=True)
    sizes = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False)
    featured_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["featured_order", "-is_featured", "name"]

    def __str__(self):
        return f"{self.name} ({self.brand})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def category_name(self):
        return self.category.name

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((1 - self.price / self.old_price) * 100)
        return None


class Wishlist(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} ♥ {self.product_id}"


class ProductLike(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_likes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"like:{self.user_id}->{self.product_id}"


class Review(TimeStampedModel):
    """A unified review: top-level (rating + comment) or a reply.

    Rules:
      • Top-level review: parent is NULL, rating REQUIRED (1..5).
      • Reply: parent is set, rating IGNORED.
      • A user can leave at most one top-level review per product.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                condition=models.Q(parent__isnull=True),
                name="uniq_top_review_per_user_product",
            )
        ]
        indexes = [
            models.Index(fields=["product", "parent"]),
        ]

    def __str__(self):
        kind = "reply" if self.parent_id else f"{self.rating}★"
        return f"{kind} by {self.user_id} on {self.product_id}"

    @property
    def is_reply(self):
        return self.parent_id is not None
