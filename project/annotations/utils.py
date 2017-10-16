import datetime
import operator
import pytz

from django.contrib.auth.models import User
from django.utils import timezone
from accounts.utils import get_robot_user, is_robot_user, get_alleviate_user
from annotations.models import Annotation
from images.model_utils import PointGen
from images.models import Image, Point
from labels.models import Label


def purge_annotations(image_id):
    """
    Goes through all point for this image and cleans up duplicate annotations.
    This should not be needed, but due to race-conditions of the backend and annotation tools
    it happens sometimes. When we catch it, this method can be called to clean up the mess.
    """
    image = Image.objects.get(pk=image_id)

    for point in Point.objects.filter(image=image):
        anns = Annotation.objects.filter(point=point)
        if len(anns) > 1:
            # Iterate through and remove any robot annotations
            for ann in anns:
                if ann.user == get_robot_user():
                    ann.delete()

            # If there are still excess annotations, simply remove the human annotations one by one.
            anns = Annotation.objects.filter(point=point)
            while anns.count() > 1:
                anns[0].delete()
                anns = Annotation.objects.filter(point=point)

    # Update the image status
    image.confirmed = image_annotation_all_done(image)
    image.save()


def image_annotation_all_done(image):
    """
    Return True if all of the image's annotation points are human annotated.
    Return False otherwise.
    Don't use image.confirmed.  That field depends
    on this function, not the other way around!
    """
    annotations = Annotation.objects.filter(image=image)

    # If every point has an annotation, and all annotations are by humans,
    # then we're all done
    return (annotations.count() == Point.objects.filter(image=image).count()
            and annotations.filter(user=get_robot_user()).count() == 0)

def image_has_any_human_annotations(image):
    """
    Return True if the image has at least one human-made Annotation.
    Return False otherwise.
    """
    human_annotations = Annotation.objects.filter(image=image).exclude(user=get_robot_user()).exclude(user=get_alleviate_user())
    return human_annotations.count() > 0

def image_annotation_area_is_editable(image):
    """
    Returns True if the image's annotation area is editable; False otherwise.
    The annotation area is editable only if:
    (1) there are no human annotations for the image yet, and
    (2) the points are not imported.
    """
    return (not image_has_any_human_annotations(image))\
    and (PointGen.db_to_args_format(image.point_generation_method)['point_generation_type'] != PointGen.Types.IMPORTED)


def get_labels_with_annotations_in_source(source):
    return Label.objects.filter(annotation__source=source).distinct()


def get_annotation_user_display(anno):
    """
    anno - an annotations.Annotation model.

    Returns a string representing the user who made the annotation.
    """
    if not anno.user:
        return "(Unknown user)"

    elif is_robot_user(anno.user):
        if not anno.robot_version:
            return "(Robot, unknown version)"
        return "Robot {v}".format(v=anno.robot_version)

    else:
        return anno.user.username


def get_annotation_version_user_display(anno_version, date_created):
    """
    anno_version - a reversion.Version model; a previous or current version
    of an annotations.Annotation model.
    date_created - creation date of the Version.

    Returns a string representing the user who made the annotation.
    """
    user_id = anno_version.field_dict['user']
    user = User.objects.get(pk=user_id)

    if not user:
        return "(Unknown user)"

    elif is_robot_user(user):
        # This check may be needed because Annotation didn't
        # originally save robot versions.
        if not anno_version.field_dict.has_key('robot_version'):
            return "(Robot, unknown version)"

        robot_version_id = anno_version.field_dict['robot_version']
        if not robot_version_id:
            return "(Robot, unknown version)"

        # On this date/time in UTC, CoralNet alpha had ended and CoralNet beta
        # robot runs had not yet started.
        beta_start_dt_naive = datetime.datetime(2016, 11, 20, 2)
        beta_start_dt = timezone.make_aware(
            beta_start_dt_naive, pytz.timezone("UTC"))

        if date_created < beta_start_dt:
            # Alpha
            return "Robot alpha-{v}".format(v=robot_version_id)

        # Beta (versions had reset, hence the need for alpha/beta distinction)
        return "Robot {v}".format(v=robot_version_id)

    else:
        return user.username


def apply_alleviate(image_id, label_probabilities):
    """
    Apply alleviate to a particular image: auto-accept top machine suggestions
    based on the confidence threshold.

    :param image_id: id of the image.
    :param label_probabilities: the machine's assigned label
           probabilities for each point of the image.
    :return: nothing.
    """
    img = Image.objects.get(id=image_id)
    source = img.source
    robot = source.get_latest_robot()
    
    if source.confidence_threshold > 99:
        return
    
    machine_annos = Annotation.objects.filter(image=img, user=get_robot_user())
    alleviate_was_applied = False

    for anno in machine_annos:
        pt_number = anno.point.point_number
        label_scores = label_probabilities[pt_number]
        descending_scores = sorted(label_scores, key=operator.itemgetter('score'), reverse=True)
        top_score = descending_scores[0]['score']
        top_confidence = top_score

        if top_confidence >= source.confidence_threshold:
            # Save the annotation under the username Alleviate, so that it's no longer
            # a robot annotation.
            anno.user = get_alleviate_user()
            anno.save()
            alleviate_was_applied = True

    if alleviate_was_applied:
        # Are all points human annotated now?
        all_done = image_annotation_all_done(img)
        # Update image status, if needed
        if all_done:
            img.confirmed = True
            img.save()


