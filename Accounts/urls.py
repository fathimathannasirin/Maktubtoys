from django.urls import path,include
from . import views

urlpatterns =[
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    
    
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/', views.resetPassword, name='resetPassword'),

    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('Change_Password/', views.Change_Password, name='Change_Password'),
    path('order_detail/<str:order_id>/', views.order_detail, name='order_detail'),

    path('contact-us/', views.contact_us, name='contact_us'),
    path('return-refund-policy/', views.return_refund_policy, name='return_refund_policy'),
    path('contact_info/', views.contact_info, name='contact_info'),
    path('terms_of_service/', views.terms_of_service, name='terms_of_service'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),

]

