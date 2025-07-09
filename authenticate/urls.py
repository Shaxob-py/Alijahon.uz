from django.urls import path

from authenticate.views import LoginTemplateView

urlpatterns = [
    path('', LoginTemplateView.as_view(),name='home'),

]








