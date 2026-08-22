from .models import Announcement, Banner, PromoBanner


def announcements(request):
    return {
        'announcements': Announcement.objects.filter(is_active=True).order_by('order', 'created_at'),
        'banners': Banner.objects.filter(is_active=True).order_by('order', 'created_at'),
        'promo_banners': PromoBanner.objects.filter(is_active=True).order_by('created_at'),
    }
