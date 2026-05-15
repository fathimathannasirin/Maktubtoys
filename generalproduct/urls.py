"""generalproduct URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns 

# 1. Non-translatable URLs (Keep these outside i18n_patterns)
urlpatterns = [
    path('admin_tools_stats/', include('admin_tools_stats.urls')),
    path('admin_tools/', include('admin_tools.urls')),
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('i18n/', include('django.conf.urls.i18n')), # Required for language switching
    
]

# 2. Translatable URLs (Wrapped in i18n_patterns)
urlpatterns += i18n_patterns(
    path('securelogin/', admin.site.urls),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accounts/', include('Accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('orders/', include('orders.urls')),
    
    # Set prefix_default_language=False if you want the default language (e.g., English) 
    # to NOT have a prefix (e.g., just /store/ instead of /en/store/)
    prefix_default_language=True 
)

# 3. Static and Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
