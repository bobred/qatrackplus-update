# import imghdr
import filetype
import logging
import os
import os.path
import shutil
import time
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

import qatrack.faults.models as faultsm
import qatrack.parts.models as partsm
import qatrack.qa.models as qam
import qatrack.service_log.models as slm

logger = logging.getLogger('qatrack')


def get_upload_path(instance, name):
    name = name.rsplit(".", 1)
    if len(name) == 1:
        name.append("")
    name, ext = name

    name_parts = (
        slugify(name),
        "%s" % (timezone.now().date(),),
        str(uuid4())[:6],
    )

    filename = "_".join(name_parts) + ("." + ext if ext else "")
    return os.path.join(settings.TMP_UPLOAD_PATH, filename)


def move_tmp_file(attach, save=True, force=False, new_name=None):
    """Move from temp location to permanent location"""

    if attach.finalized and not force:
        return

    start_path = attach.attachment.path
    name_parts = [
        attach.type,
        str(attach.owner.pk),
        new_name or os.path.basename(attach.attachment.name),
    ]
    new_path = os.path.join(settings.UPLOAD_ROOT, *name_parts)

    if not os.path.exists(os.path.dirname(new_path)):
        os.makedirs(os.path.dirname(new_path))

    # windows sometimes complains about the file being open
    # in another process when deleting, so rather than moving the file
    # we will copy and then remove the old file, ignoring errors which
    # occur when deleting the file from the tmp location
    shutil.copy(start_path, new_path)
    count = 0
    while True:
        try:
            attach.attachment.close()
            os.remove(start_path)
            break
        except PermissionError:
            if count == 2:
                logger.error("Failed to remove %s when moving %s to %s." % (start_path, start_path, new_path))
                break
            count += 1
            time.sleep(0.2)

    new_name = "uploads/" + '/'.join(name_parts)
    attach.attachment.name = new_name

    if save:
        attach.save()


class Attachment(models.Model):

    attachment = models.FileField(verbose_name=_l("Attachment"), upload_to=get_upload_path, max_length=255)
    label = models.CharField(verbose_name=_l("Label"), max_length=255, blank=True)
    comment = models.TextField(verbose_name=_l("Comment"), blank=True)

    test = models.ForeignKey(qam.Test, on_delete=models.CASCADE, null=True, blank=True)
    testlist = models.ForeignKey(qam.TestList, on_delete=models.CASCADE, null=True, blank=True)
    testlistcycle = models.ForeignKey(qam.TestListCycle, on_delete=models.CASCADE, null=True, blank=True)
    testinstance = models.ForeignKey(qam.TestInstance, on_delete=models.CASCADE, null=True, blank=True)
    testlistinstance = models.ForeignKey(qam.TestListInstance, on_delete=models.CASCADE, null=True, blank=True)
    serviceevent = models.ForeignKey(slm.ServiceEvent, on_delete=models.CASCADE, null=True, blank=True)
    part = models.ForeignKey(partsm.Part, on_delete=models.CASCADE, null=True, blank=True)
    fault = models.ForeignKey(faultsm.Fault, on_delete=models.CASCADE, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)

    OWNER_MODELS = [
        "test",
        "testlist",
        "testlistcycle",
        "testinstance",
        "testlistinstance",
        "serviceevent",
        "part",
        "fault",
    ]

    @property
    def _possible_owners(self):
        return [getattr(self, a) for a in self.OWNER_MODELS]

    @property
    def owner(self):
        """Foreign key object that owns this attachment"""
        try:
            return next(o for o in self._possible_owners if o)
        except StopIteration:
            return None

    @property
    def type(self):
        """Model type of foreign owner e.g. 'testlist' or 'unittestcollection'"""
        if self.owner is not None:
            return self.owner._meta.model_name

    def move_tmp_file(self, save=True, force=False):
        """Move from temp location to permanent location"""

        return move_tmp_file(self, save=save, force=force)

    @property
    def has_owner(self):
        """Return bool indicating whether this attachment is owned or not"""
        return bool(self.owner and self.owner.pk)

    @property
    def is_in_tmp(self):
        """Return bool indicating whether this attachment is currently in staging area"""
        return settings.TMP_UPLOAD_ROOT in self.attachment.path

    @property
    def finalized(self):
        """Return bool indicating whether this has been finalized yet"""
        return self.has_owner and not self.is_in_tmp

    @property
    def can_finalize(self):
        """Return bool indicating whether this file is ready to be finalized"""
        return self.has_owner and self.is_in_tmp

    def save(self, *args, **kwargs):
        """Save model and move it to final location if possible"""

        super(Attachment, self).save(*args, **kwargs)

        if self.can_finalize:
            self.move_tmp_file()

    def clean(self):
        nowners = sum(1 for o in self._possible_owners if o)
        if nowners > 1:
            raise ValidationError(_l("An attachment should only have one owner"))

    @property
    def is_image(self):

        try:
            img = filetype.guess(self.attachment) is not None
            # img = imghdr.what(self.attachment) is not None
        except FileNotFoundError:
            return False
        ext = os.path.splitext(self.attachment.name)[1].strip(".")
        displayable = ["jpg", "jpeg", "png", "svg", "bmp", "gif"]
        force = ext in displayable
        is_img = img in displayable
        return is_img or force

    def __str__(self):
        return "%s(%s, %s)" % (_("Attachment"), self.owner or _("No Owner"), self.attachment.name)
