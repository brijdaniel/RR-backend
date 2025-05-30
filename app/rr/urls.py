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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import *


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path("api/checklists/", ChecklistListCreateView.as_view(), name="checklists"),
    path("api/checklists/<int:pk>/regrets/", RegretListCreateView.as_view(), name="regrets"),
    path("api/checklists/<int:pk>/regrets/<int:id>/", RegretRetrieveUpdateView.as_view(), name="update_regrets"),
]


# swagger urls
urlpatterns += [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(template_name="swagger-ui.html", url_name="schema"), name="swagger-ui"),
    ]
