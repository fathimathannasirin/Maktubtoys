from django.db import models
from category.models import Category


class Announcement(models.Model):
    text = models.CharField(max_length=220, help_text="Message to display in the scrolling announcement bar")
    is_active = models.BooleanField(default=True, help_text="Show this message on the site")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'

    def __str__(self):
        return self.text[:70]


class Banner(models.Model):
    title = models.CharField(max_length=120, blank=True, help_text="Optional title shown on the banner")
    subtitle = models.CharField(max_length=220, blank=True, help_text="Optional subtitle or CTA")
    image = models.ImageField(upload_to='banners/', help_text='Upload banner image (recommended 1600x600)')
    link = models.URLField(blank=True, help_text='Optional link when the banner is clicked')
    is_active = models.BooleanField(default=True, help_text='Show this banner on the site')
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'

    def __str__(self):
        return self.title or (self.subtitle[:50] if self.subtitle else self.image.name)


class SectionOfferBanner(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='section_offer_banners',
        help_text='Optional: choose a parent category to show this banner after that section. Leave empty for global rotation.',
    )
    title = models.CharField(max_length=120, blank=True, help_text='Optional title shown on the offer banner')
    subtitle = models.CharField(max_length=220, blank=True, help_text='Optional subtitle or short offer text')
    image = models.ImageField(upload_to='banners/section_offers/', help_text='Upload offer banner image')
    link = models.URLField(blank=True, help_text='Optional link when the offer banner is clicked')
    is_active = models.BooleanField(default=True, help_text='Show this banner on the homepage')
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Section Offer Banner'
        verbose_name_plural = 'Section Offer Banners'

    def __str__(self):
        category_name = self.category.category_name if self.category else 'Global'
        label = self.title or self.subtitle or self.image.name
        return f'{category_name}: {label}'

class PromoBanner(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='banners/')
    link_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"