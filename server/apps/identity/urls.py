from django.urls import path

from . import views

urlpatterns = [
    path("auth/password", views.PasswordLoginView.as_view()),
    path("auth/csrf", views.CsrfView.as_view()),
    path("auth/otp/request", views.RequestCodeView.as_view()),
    path("auth/otp/verify", views.VerifyCodeView.as_view()),
    path("auth/refresh", views.RefreshView.as_view()),
    path("auth/logout", views.LogoutView.as_view()),
    path("auth/me", views.MeView.as_view()),
    path("staff/users", views.UsersView.as_view()),
    path("staff/users/<uuid:identifier>", views.UserDetailView.as_view()),
    path("staff/sessions/<uuid:identifier>/revoke", views.RevokeSessionView.as_view()),
]
