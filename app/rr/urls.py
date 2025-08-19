"""
URL configuration for rr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import *


# Admin panel
urlpatterns = [
    path('admin/', admin.site.urls),
]

# Simple JWT
urlpatterns += [
    path('auth/user/', UserLoginOrRegisterView.as_view(), name='login_or_register'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# API
urlpatterns += [
    path("api/checklists/", ChecklistListCreateView.as_view(), name="checklists"),
    path("api/checklists/<int:pk>/regrets/", RegretListCreateView.as_view(), name="regrets"),
    path("api/checklists/<int:pk>/regrets/<int:id>/", RegretRetrieveUpdateView.as_view(), name="update_regrets"),
]

# Network API
urlpatterns += [
    path("api/network/validate/<str:username>/", NetworkValidationView.as_view(), name="network_validate"),
    path("api/network/follow/<str:username>/", NetworkFollowView.as_view(), name="network_follow"),
    path("api/network/unfollow/<str:username>/", NetworkUnfollowView.as_view(), name="network_unfollow"),
    path("api/network/list/<str:list_type>/", NetworkListView.as_view(), name="network_list"),
    path("api/network/settings/", NetworkSettingsView.as_view(), name="network_settings"),
]


# Swagger
urlpatterns += [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(template_name="swagger-ui.html", url_name="schema"), name="swagger-ui"),
    ]
