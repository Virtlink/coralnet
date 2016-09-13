from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_comma_separated_integer_list
from django.forms import Form
from django.forms.fields import CharField
from django.forms.models import ModelForm
from django.forms.widgets import TextInput, HiddenInput
from django.utils.html import escape
from .models import Label, LabelSet, LocalLabel


class LabelForm(ModelForm):
    class Meta:
        model = Label
        fields = ['name', 'default_code', 'group', 'description', 'thumbnail']
        widgets = {
            'default_code': TextInput(attrs={'size': 10}),
        }

    def clean_name(self):
        """
        Add an error if the specified name matches that of an existing label.
        """
        name = self.cleaned_data['name']

        try:
            # Case-insensitive compare
            existing_label = Label.objects.get(name__iexact=name)
        except Label.DoesNotExist:
            # Name is not taken
            pass
        else:
            # Name is taken
            msg = (
                'There is already a label with the same name:'
                ' <a href="{url}" target="_blank">'
                '{existing_name}</a>').format(
                    url=reverse('label_main', args=[existing_label.pk]),
                    # Use escape to prevent XSS, since label names are in
                    # general user defined
                    existing_name=escape(existing_label.name),
                )
            raise ValidationError(msg)

        return name

    # No check for Labels with the same default code. We only care about
    # LabelSets having unique LocalLabel codes.


class LabelSetForm(Form):
    label_ids = CharField(
        validators=[validate_comma_separated_integer_list],
        required=True,
        widget=HiddenInput(),
        error_messages=dict(required="You must select one or more labels."),
    )

    def __init__(self, *args, **kwargs):
        self.source = kwargs.pop('source')
        super(LabelSetForm, self).__init__(*args, **kwargs)

        if self.source.labelset:
            id_values_list = \
                self.source.labelset.get_globals().values_list('pk', flat=True)
            self.initial['label_ids'] = \
                ','.join(str(pk) for pk in id_values_list)
        else:
            self.initial['label_ids'] = ''

    def clean_label_ids(self):
        # Run through a set to remove dupes, then get a list again
        label_id_list = list(set(
            int(pk) for pk in self.cleaned_data['label_ids'].split(',')))

        # Check if labels of these ids exist
        bad_id_list = []
        for label_id in label_id_list:
            try:
                Label.objects.get(pk=label_id)
            except Label.DoesNotExist:
                bad_id_list.append(label_id)

        if bad_id_list:
            msg = (
                "Could not find labels of ids: {bad_ids}."
                " Either we messed up, or one of the"
                " labels you selected just got deleted."
                " If the problem persists,"
                " please contact the site admins.").format(
                    bad_ids=", ".join(str(n) for n in bad_id_list),
                )
            raise ValidationError(msg)

        # TODO: Check that there's at least 1 valid label id.
        # TODO: Check if any in-use labels are marked for removal.

        # Return the integer list (rather than its string repr).
        return label_id_list

    def get_error(self):
        # Find the first error and return it.
        # Since this form has only one field, we won't specify
        # the field in the message.
        message = None
        for _, error_messages in self.errors.iteritems():
            if error_messages:
                message = error_messages[0]
        return message

    def save_labelset(self):
        """
        Call this after validation to save the labelset.
        """
        pending_global_ids = set(self.cleaned_data['label_ids'])
        labelset_was_created = False

        if not self.source.labelset:
            labelset = LabelSet()
            labelset.save()
            self.source.labelset = labelset
            self.source.save()
            labelset_was_created = True

        labelset = self.source.labelset
        existing_global_ids = set(
            labelset.get_globals().values_list('pk', flat=True))

        global_ids_to_delete = existing_global_ids - pending_global_ids
        local_labels_to_delete = labelset.get_labels().filter(
                global_label__pk__in=global_ids_to_delete)
        local_labels_to_delete.delete()

        global_ids_to_add = pending_global_ids - existing_global_ids
        local_labels_to_add = []
        for global_id in global_ids_to_add:
            global_label = Label.objects.get(pk=global_id)
            # TODO: Detect label code conflicts with others in the labelset,
            # and adapt.
            # e.g. 'Soft' -> 'Soft2', 'Bare_Subst' -> 'Bare_Subs2', etc.
            local_label = LocalLabel(
                code=global_label.default_code,
                global_label=global_label,
                labelset=labelset,
            )
            local_labels_to_add.append(local_label)
        LocalLabel.objects.bulk_create(local_labels_to_add)

        return labelset_was_created
