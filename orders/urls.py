from django.urls import path,include
from . import views

urlpatterns =[
    path('place_order', views.place_order, name='place_order'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('track_order/',views.track_order,name='track_order'),
    path('return-request/<int:order_id>/', views.return_request, name='return_request'),
    path('print-parcel/<int:parcel_id>/', views.print_single_parcel, name='print_single_parcel'),
    path('print-full-invoice/<int:order_id>/', views.print_full_invoice, name='print_full_invoice'),
   
]