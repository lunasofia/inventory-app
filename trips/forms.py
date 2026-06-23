from django import forms

from catalog.models import Category

from accounts.models import User

from .models import Bag, PackingItem, Template, TemplateItem, TemplateShare, Trip, TripShare


class TripForm(forms.ModelForm):
    # Non-model field: optionally start a new trip from a template (create only).
    start_from_template = forms.ModelChoiceField(
        queryset=Template.objects.none(), required=False, empty_label='Start blank',
        label='Start from template',
    )

    class Meta:
        model = Trip
        fields = ('name', 'destination', 'start_date', 'end_date', 'status', 'notes')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, owner=None, show_template=False, **kwargs):
        super().__init__(*args, **kwargs)
        if show_template and owner is not None:
            self.fields['start_from_template'].queryset = Template.accessible_by(owner)
        else:
            del self.fields['start_from_template']

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'End date cannot be before the start date.')
        return cleaned


class TemplateForm(forms.ModelForm):
    """Create/rename a template. Names are unique (case-insensitive) per owner."""

    class Meta:
        model = Template
        fields = ('name', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Template name is required.')
        dupes = Template.objects.filter(owner=self.owner, name__iexact=name)
        if self.instance.pk:
            dupes = dupes.exclude(pk=self.instance.pk)
        if dupes.exists():
            raise forms.ValidationError('You already have a template with that name.')
        return name


class TemplateItemForm(forms.ModelForm):
    """Add/edit a template line. Category choices scoped to the acting user."""

    class Meta:
        model = TemplateItem
        fields = ('name', 'quantity', 'category')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add an item…', 'autocomplete': 'off'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'qty'}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'Uncategorized'
        self.fields['quantity'].required = False
        if owner is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=owner)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Item name is required.')
        return name

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is None:
            return 1
        if qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return qty


class PackingItemForm(forms.ModelForm):
    """Add/edit a packing line. Category choices are scoped to the acting user;
    bag choices are scoped to the trip."""

    class Meta:
        model = PackingItem
        fields = ('name', 'quantity', 'category', 'bag')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add an item…', 'autocomplete': 'off'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'qty'}),
        }

    def __init__(self, *args, owner=None, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'Uncategorized'
        self.fields['bag'].required = False
        self.fields['bag'].empty_label = 'Unbagged'
        # A blank quantity defaults to 1 (see clean_quantity).
        self.fields['quantity'].required = False
        if owner is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=owner)
        self.fields['bag'].queryset = trip.bags.all() if trip is not None else Bag.objects.none()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Item name is required.')
        return name

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is None:
            return 1  # blank defaults to 1
        if qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return qty


class CategoryForm(forms.ModelForm):
    """Add/rename a category. Rename enforces case-insensitive uniqueness per
    owner; add dedupes by reusing an existing same-name category (in the view)."""

    class Meta:
        model = Category
        fields = ('name',)
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'Add a category…', 'autocomplete': 'off'})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        if self.instance.pk:  # rename: must stay unique
            dupes = Category.objects.filter(owner=self.owner, name__iexact=name).exclude(pk=self.instance.pk)
            if dupes.exists():
                raise forms.ValidationError('You already have a category with that name.')
        return name


class BagForm(forms.ModelForm):
    """Create/rename a bag. Names are unique (case-insensitive) per trip."""

    class Meta:
        model = Bag
        fields = ('name',)
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'Add a bag…', 'autocomplete': 'off'})}

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Bag name is required.')
        dupes = Bag.objects.filter(trip=self.trip, name__iexact=name)
        if self.instance.pk:
            dupes = dupes.exclude(pk=self.instance.pk)
        if dupes.exists():
            raise forms.ValidationError('You already have a bag with that name.')
        return name


class TemplateShareForm(forms.Form):
    """Share a template with a registered user by email, with view/edit permission."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'collaborator@email.com', 'autocomplete': 'off',
    }))
    permission = forms.ChoiceField(
        choices=TemplateShare.Permission.choices, initial=TemplateShare.Permission.EDIT,
    )

    def __init__(self, *args, template=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip()
        if not email:
            return cleaned
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            self.add_error('email', 'No Packwell account with that email.')
        elif self.template and user == self.template.owner:
            self.add_error('email', 'You already own this template.')
        else:
            cleaned['user'] = user
        return cleaned


class TripShareForm(forms.Form):
    """Share a trip with a registered user by email, with view/edit permission."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'collaborator@email.com', 'autocomplete': 'off',
    }))
    permission = forms.ChoiceField(
        choices=TripShare.Permission.choices, initial=TripShare.Permission.EDIT,
    )

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip()
        if not email:
            return cleaned
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            self.add_error('email', 'No Packwell account with that email.')
        elif self.trip and user == self.trip.owner:
            self.add_error('email', 'You already own this trip.')
        else:
            cleaned['user'] = user
        return cleaned


class ReminderForm(forms.Form):
    """Add a reminder (used for default / template / trip reminder lists)."""

    text = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Add a reminder…', 'autocomplete': 'off'}),
    )

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise forms.ValidationError('Reminder text is required.')
        return text
