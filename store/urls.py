from django.urls import path,include
from . import views

urlpatterns =[
    path('', views.store, name='store'),
    path('search/', views.search, name='search'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('check-unique/', views.check_unique, name='check_unique'),
    path('get-product-price/', views.get_product_price, name='get_product_price'),
    path('get-product-data/', views.get_product_data, name='get_product_data'),
    path('get-product-cost/', views.get_product_cost, name='get_product_cost'),
    path('api/purchase-items/', views.get_purchase_items, name='get_purchase_items'),
]
