from django.db import models


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
