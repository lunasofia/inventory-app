from django import forms

from catalog.models import Category

from .models import PackingItem, Trip


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
    """Add/edit a packing line. Category choices are scoped to the acting user."""

    class Meta:
        model = PackingItem
        fields = ('name', 'quantity', 'category')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add an item…', 'autocomplete': 'off'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'qty'}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'Uncategorized'
        if owner is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=owner)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Item name is required.')
        return name

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty is None or qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return qty
