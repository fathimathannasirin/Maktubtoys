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
from django.http import HttpResponse
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns 

admin.site.site_header = "MAKTUB Toys"  # Admin Header
admin.site.site_title = "MAKTUB Toys Admin Portal"     # Browser Tab
admin.site.index_title = "Welcome to MAKTUB Toys Admin Dashboard" # Admin Home


def sitemap_xml(request):
    try:
        from category.models import Category
        from store.models import Product

        domain = "https://maktubtoys.com"
        urls = [
            {"loc": f"{domain}/", "priority": "1.0", "changefreq": "daily"},
            {"loc": f"{domain}/store/", "priority": "0.9", "changefreq": "daily"},
            {"loc": f"{domain}/accounts/contact-us/", "priority": "0.7", "changefreq": "monthly"},
            {"loc": f"{domain}/accounts/return-refund-policy/", "priority": "0.5", "changefreq": "monthly"},
            {"loc": f"{domain}/accounts/shipping-policy/", "priority": "0.5", "changefreq": "monthly"},
            {"loc": f"{domain}/accounts/terms_of_service/", "priority": "0.5", "changefreq": "monthly"},
        ]

        # Categories
        for cat in Category.objects.all():
            urls.append({
                "loc": f"{domain}{cat.get_url()}",
                "priority": "0.8",
                "changefreq": "weekly"
            })

        # Available Products
        for prod in Product.objects.filter(is_available=True):
            urls.append({
                "loc": f"{domain}{prod.get_url()}",
                "priority": "0.8",
                "changefreq": "weekly"
            })

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]
        for item in urls:
            xml_lines.append('   <url>')
            xml_lines.append(f'      <loc>{item["loc"]}</loc>')
            xml_lines.append(f'      <priority>{item["priority"]}</priority>')
            xml_lines.append(f'      <changefreq>{item["changefreq"]}</changefreq>')
            xml_lines.append('   </url>')
        xml_lines.append('</urlset>')
        xml_content = "\n".join(xml_lines)
    except Exception:
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url>
      <loc>https://maktubtoys.com/</loc>
      <priority>1.0</priority>
      <changefreq>daily</changefreq>
   </url>
   <url>
      <loc>https://maktubtoys.com/store/</loc>
      <priority>0.9</priority>
      <changefreq>daily</changefreq>
   </url>
</urlset>"""
    return HttpResponse(xml_content, content_type="application/xml")


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /securelogin/\n"
        "Disallow: /cart/\n"
        "Disallow: /orders/\n\n"
        "Sitemap: https://maktubtoys.com/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")


# 1. Non-translatable URLs (Keep these outside i18n_patterns)
urlpatterns = [
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap_xml, name='sitemap'),
    path('admin_tools/', include('admin_tools.urls')),
    # path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),  # Disabled
    path('i18n/', include('django.conf.urls.i18n')),  # Required for language switching
]


# 2. Translatable URLs (Wrapped in i18n_patterns)
urlpatterns += i18n_patterns(
    path('securelogin/stats/', views.admin_stats_dashboard, name='admin_stats_dashboard'),
    path('securelogin/', admin.site.urls),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accounts/', include('Accounts.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('orders/', include('orders.urls')),
    
    # Set prefix_default_language=False so the default language (English) 
    # does NOT redirect (e.g. https://maktubtoys.com/ instead of /en/), allowing search engines to index directly.
    prefix_default_language=False 
)

# 3. Static and Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
