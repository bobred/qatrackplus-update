import json

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils.formats import get_format

from qatrack.parts.models import PartStorageCollection, PartUsed
from qatrack.qa.models import TestListInstance, UnitTestCollection
from qatrack.service_log.models import (
    ReturnToServiceQA,
    ServiceEvent,
    ServiceEventStatus,
)
from qatrack.units.models import Unit

cache.delete(settings.CACHE_UNREVIEWED_COUNT)
cache.delete(settings.CACHE_UNREVIEWED_COUNT_USER)
cache.delete(settings.CACHE_RTS_QA_COUNT)
cache.delete(settings.CACHE_RTS_INCOMPLETE_QA_COUNT)
cache.delete(settings.CACHE_DEFAULT_SE_STATUS)
cache.delete(settings.CACHE_SE_NEEDING_REVIEW_COUNT)
cache.delete(settings.CACHE_IN_PROGRESS_COUNT_USER)
cache.delete(settings.CACHE_SERVICE_STATUS_COLOURS)


@receiver(pre_delete, sender=PartUsed)
def update_part_storage_quantity(*args, **kwargs):
    pu = kwargs['instance']
    part = pu.part
    storage = pu.from_storage
    quantity = pu.quantity
    # Return parts used to storage:
    if storage:
        try:
            psc = PartStorageCollection.objects.get(part=part, storage=storage)
            psc.quantity += quantity
            psc.save()
        except ObjectDoesNotExist:
            pass


@receiver(post_delete, sender=PartStorageCollection)
def update_part_quantity(*args, **kwargs):

    psc = kwargs['instance']
    part = psc.part
    part.set_quantity_current()


@receiver(post_save, sender=TestListInstance)
@receiver(post_delete, sender=TestListInstance)
@receiver(post_save, sender=User)
@receiver(post_save, sender=Group)
def update_unreviewed_cache(*args, **kwargs):
    """When a test list is completed invalidate the unreviewed counts"""
    cache.delete(settings.CACHE_UNREVIEWED_COUNT)
    cache.delete(settings.CACHE_UNREVIEWED_COUNT_USER)
    cache.delete(settings.CACHE_RTS_QA_COUNT)
    cache.delete(settings.CACHE_RTS_INCOMPLETE_QA_COUNT)
    cache.delete(settings.CACHE_IN_PROGRESS_COUNT_USER)


@receiver(post_save, sender=ReturnToServiceQA)
@receiver(post_delete, sender=ReturnToServiceQA)
def update_rts_cache(*args, **kwargs):
    """When a RTS is completed invalidate the unreviewed counts"""
    cache.delete(settings.CACHE_RTS_QA_COUNT)
    cache.delete(settings.CACHE_RTS_INCOMPLETE_QA_COUNT)


@receiver(post_save, sender=ServiceEventStatus)
@receiver(post_delete, sender=ServiceEventStatus)
@receiver(post_delete, sender=ServiceEvent)
def update_se_cache(*args, **kwargs):
    """When a service status is changed invalidate the default and review count"""
    cache.delete(settings.CACHE_DEFAULT_SE_STATUS)
    cache.delete(settings.CACHE_SE_NEEDING_REVIEW_COUNT)


@receiver(post_save, sender=UnitTestCollection)
@receiver(post_delete, sender=UnitTestCollection)
def update_active_unit_test_collections_for_unit_utc(*args, **kwargs):
    unit = kwargs['instance'].unit
    qs = UnitTestCollection.objects.filter(
        unit=unit,
        active=True
    ).order_by('name')
    cache.set(settings.CACHE_ACTIVE_UTCS_FOR_UNIT_.format(unit.id), qs)


@receiver(post_save, sender=Unit)
@receiver(post_delete, sender=Unit)
def update_active_unit_test_collections_for_unit(*args, **kwargs):
    unit = kwargs['instance']
    qs = UnitTestCollection.objects.filter(
        unit=unit,
        active=True
    ).order_by('name')
    cache.set(settings.CACHE_ACTIVE_UTCS_FOR_UNIT_.format(unit.id), qs)


@receiver(post_save, sender=ServiceEventStatus)
@receiver(post_delete, sender=ServiceEventStatus)
def update_colours(*args, **kwargs):
    service_status_colours = {ses.name: ses.colour for ses in ServiceEventStatus.objects.all()}
    cache.set(settings.CACHE_SERVICE_STATUS_COLOURS, service_status_colours)


def site(request):
    cur_site = get_current_site(request)

    unreviewed = cache.get(settings.CACHE_UNREVIEWED_COUNT)
    if unreviewed is None:
        unreviewed = TestListInstance.objects.unreviewed_count()
        cache.set(settings.CACHE_UNREVIEWED_COUNT, unreviewed)

    se_unreviewed_rts = cache.get(settings.CACHE_RTS_QA_COUNT)
    if se_unreviewed_rts is None:
        se_unreviewed_rts = ReturnToServiceQA.objects.filter(
            test_list_instance__isnull=False,
            test_list_instance__all_reviewed=False
        ).count()
        cache.set(settings.CACHE_RTS_QA_COUNT, se_unreviewed_rts)

    se_incomplete_rts = cache.get(settings.CACHE_RTS_INCOMPLETE_QA_COUNT)
    if se_incomplete_rts is None:
        se_incomplete_rts = ReturnToServiceQA.objects.filter(
            test_list_instance__isnull=True,
        ).count()
        cache.set(settings.CACHE_RTS_INCOMPLETE_QA_COUNT, se_incomplete_rts)

    unreviewed_user_counts = cache.get(settings.CACHE_UNREVIEWED_COUNT_USER)
    if unreviewed_user_counts is None and hasattr(request, "user"):
        your_unreviewed = TestListInstance.objects.your_unreviewed_count(request.user)
        unreviewed_user_counts = {request.user.pk: your_unreviewed}
        cache.set(settings.CACHE_UNREVIEWED_COUNT_USER, unreviewed_user_counts)
    else:
        try:
            your_unreviewed = unreviewed_user_counts[request.user.pk]
        except KeyError:
            your_unreviewed = TestListInstance.objects.your_unreviewed_count(request.user)
            unreviewed_user_counts[request.user.pk] = your_unreviewed
            cache.set(settings.CACHE_UNREVIEWED_COUNT_USER, unreviewed_user_counts)
        except Exception:
            your_unreviewed = 0

    default_se_status = cache.get(settings.CACHE_DEFAULT_SE_STATUS)
    if default_se_status is None:
        default_se_status = ServiceEventStatus.get_default()
        cache.set(settings.CACHE_DEFAULT_SE_STATUS, default_se_status)

    service_status_colours = cache.get(settings.CACHE_SERVICE_STATUS_COLOURS)
    if service_status_colours is None:
        service_status_colours = {ses.name: ses.colour for ses in ServiceEventStatus.objects.all()}
        cache.set(settings.CACHE_SERVICE_STATUS_COLOURS, service_status_colours)

    se_needing_review_count = cache.get(settings.CACHE_SE_NEEDING_REVIEW_COUNT)
    if se_needing_review_count is None:
        se_needing_review_count = ServiceEvent.objects.filter(
            service_status__in=ServiceEventStatus.objects.filter(is_review_required=True),
            is_review_required=True,
        ).count()
        cache.set(settings.CACHE_SE_NEEDING_REVIEW_COUNT, se_needing_review_count)

    in_progress_user_counts = cache.get(settings.CACHE_IN_PROGRESS_COUNT_USER)
    if in_progress_user_counts is None and hasattr(request, "user"):
        your_in_progress = TestListInstance.objects.your_in_progress_count(request.user)
        in_progress_user_counts = {request.user.pk: your_in_progress}
        cache.set(settings.CACHE_IN_PROGRESS_COUNT_USER, in_progress_user_counts)
    else:
        try:
            your_in_progress = in_progress_user_counts[request.user.pk]
        except KeyError:
            your_in_progress = TestListInstance.objects.your_in_progress_count(request.user)
            in_progress_user_counts[request.user.pk] = your_in_progress
            cache.set(settings.CACHE_IN_PROGRESS_COUNT_USER, in_progress_user_counts)
        except Exception:
            your_in_progress = 0

    return {
        'SITE_NAME': cur_site.name,
        'SITE_URL': cur_site.domain,
        'SELF_REGISTER': settings.ACCOUNTS_SELF_REGISTER,
        'VERSION': settings.VERSION,
        'BUG_REPORT_URL': settings.BUG_REPORT_URL,
        'FEATURE_REQUEST_URL': settings.FEATURE_REQUEST_URL,
        'UNREVIEWED': unreviewed,
        'USERS_UNREVIEWED': your_unreviewed,
        'ICON_SETTINGS': settings.ICON_SETTINGS,
        'ICON_SETTINGS_JSON': json.dumps(settings.ICON_SETTINGS),
        'TEST_STATUS_SHORT_JSON': json.dumps(settings.TEST_STATUS_DISPLAY_SHORT),
        'REVIEW_DIFF_COL': settings.REVIEW_DIFF_COL,
        'DEBUG': settings.DEBUG,
        'USE_SQL_REPORTS': settings.USE_SQL_REPORTS,
        'USE_SERVICE_LOG': settings.USE_SERVICE_LOG,
        'USE_PARTS': settings.USE_PARTS,
        'USE_ISSUES': settings.USE_ISSUES,
        'DEFAULT_SE_STATUS': default_se_status,
        'SE_NEEDING_REVIEW_COUNT': se_needing_review_count,
        'SE_RTS_INCOMPLETE_QA_COUNT': se_incomplete_rts,
        'SE_RTS_UNREVIEWED_QA_COUNT': se_unreviewed_rts,
        'USERS_IN_PROGRESS': your_in_progress,

        # JavaScript Date Formats
        'MOMENT_DATE_FMT': get_format("MOMENT_DATE_FMT"),
        'MOMENT_DATETIME_FMT': get_format("MOMENT_DATETIME_FMT"),
        'FLATPICKR_DATE_FMT': get_format("FLATPICKR_DATE_FMT"),
        'FLATPICKR_DATETIME_FMT': get_format("FLATPICKR_DATETIME_FMT"),
        'DATERANGEPICKER_DATE_FMT': get_format("DATERANGEPICKER_DATE_FMT"),
    }
