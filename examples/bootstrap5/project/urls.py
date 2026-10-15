from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from project.views import HomeView


class CrispyAuthenticationForm(AuthenticationForm):
    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout("username", "password", FormActions(Submit("login", _("Log In"))))
        return helper


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("login/", LoginView.as_view(form_class=CrispyAuthenticationForm), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    # example feature apps append their include() here
]

urlpatterns += [path("datetimepicker/", include("datetimepicker.urls"))]
urlpatterns += [
    path("_typeahead/", include("crud_views_widget_typeahead.urls")),
    path("typeahead/", include("typeahead.urls")),
]
