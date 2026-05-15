from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . models import Account, UserProfile,ContactMessage
from django.utils.html import format_html

# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin_form_validation.js',)

class AccountAdmin(BaseAdmin,UserAdmin):
    list_display=( 'email','username','first_name','last_name','last_login','date_joined','is_active')
    list_display_links=('email','first_name','last_name')
    readonly_fields=('last_login','date_joined')
    ordering=('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets=()

class UserProfileAdmin(BaseAdmin,admin.ModelAdmin):
    def thumbnail(self, object):
        return format('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
    thumbnail.short_description = 'Profile Picture'
    list_display = ('thumbnail', 'user', 'street_number', 'building_number', 'zone_number')

class ContactMessageAdmin(BaseAdmin,admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at') # Make read-only so they can't be edited
    list_per_page = 20


admin.site.register(Account,AccountAdmin)
admin.site.register(UserProfile,UserProfileAdmin)
admin.site.register(ContactMessage,ContactMessageAdmin)
