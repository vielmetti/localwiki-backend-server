from django.db.models.signals import pre_save, post_save
from django.utils.translation import ugettext as _

from actstream import action

from redirects.models import Redirect

from .models import Page


def _delete_page(sender, instance, raw, **kws):
    # Delete the source page if it exists.
    if Page.objects.filter(slug=instance.source, region=instance.region):
        p = Page.objects.get(slug=instance.source, region=instance.region)
        p.delete(comment=_("Redirect created"))


def _delete_redirect(sender, instance, raw, **kws):
    if Redirect.objects.filter(source=instance.slug, region=instance.region):
        r = Redirect.objects.get(source=instance.slug, region=instance.region)
        r.delete(comment=_("Page created"))


def _created_page_action(sender, instance, created, raw, **kws):
    """
    Notify this user's followers that the page was created (via activity stream).
    """
    if not created:
        return

    user_edited = instance.versions.most_recent().version_info.user
    if not user_edited:
        return
    
    action.send(user_edited, verb='created page', action_object=instance)


# When a Redirect is created we want to delete the source Page if it
# exists.  This is so the redirect (which works via 404 fall-through)
# will be immediately functional.
pre_save.connect(_delete_page, sender=Redirect)

# When a page is created that overlaps with a Redirect we should
# delete the Redirect.
pre_save.connect(_delete_redirect, sender=Page)

post_save.connect(_created_page_action, sender=Page)
