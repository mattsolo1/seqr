"""seqr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url
import seqr.views.pages
import seqr.views.api

page_endpoints = {
    'dashboard': seqr.views.pages.dashboard,
}

api_endpoints = {
    'projects_with_stats': seqr.views.api.projects_with_stats,
    'projects': seqr.views.api.projects,
    'user': seqr.views.api.user,
}


# page api
urlpatterns = []
urlpatterns += [url("^%(url_endpoint)s$" % locals(), handler_function) for url_endpoint, handler_function in page_endpoints.items()]

# versioned api
urlpatterns += [url("^%(url_endpoint)s$" % locals(), handler_function) for url_endpoint, handler_function in api_endpoints.items()]
urlpatterns += [url("^v1/%(url_endpoint)s$" % locals(), handler_function) for url_endpoint, handler_function in api_endpoints.items()]
