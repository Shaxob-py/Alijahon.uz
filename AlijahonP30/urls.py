from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, include
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language

from AlijahonP30.settings import MEDIA_ROOT, MEDIA_URL


def force_lang_prefix(path, lang_code):
    path_split = path.split('/')
    path_split[3] = lang_code
    path = "/".join(path_split)
    return path


def set_language(request):
    next_url = request.POST.get("next", request.GET.get("next"))
    if (
            next_url or request.accepts("text/html")
    ) and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = request.META.get("HTTP_REFERER")
        if not url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
        ):
            next_url = "/"
    response = HttpResponseRedirect(next_url) if next_url else HttpResponse(status=204)
    if request.method == "POST":
        lang_code = request.POST.get("language")
        if lang_code and check_for_language(lang_code):
            if next_url:
                next_trans = force_lang_prefix(next_url, lang_code)
                if next_trans != next_url:
                    response = HttpResponseRedirect(next_trans)
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                lang_code,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
    return response


urlpatterns = [
                  path("i18n/set_lang/", set_language, name="set_language"),
                  path('accounts/', include('allauth.urls')),
                  path('ckeditor/', include('ckeditor_uploader.urls')),
              ] + static(MEDIA_URL, document_root=MEDIA_ROOT) + i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include("apps.urls")),
)
