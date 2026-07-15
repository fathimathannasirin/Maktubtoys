from .models import Announcement, Banner


def announcements(request):
    return {
        'announcements': Announcement.objects.filter(is_active=True).order_by('order', 'created_at'),
        'banners': Banner.objects.filter(is_active=True).order_by('order', 'created_at')
    }
