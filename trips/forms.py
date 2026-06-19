from django import forms

from catalog.models import Category

from .models import Bag, PackingItem, Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ('name', 'destination', 'start_date', 'end_date', 'status', 'notes')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'End date cannot be before the start date.')
        return cleaned


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
