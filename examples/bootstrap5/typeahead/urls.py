from typeahead.views import cv_task, cv_team

urlpatterns = cv_team.urlpatterns + cv_task.urlpatterns
