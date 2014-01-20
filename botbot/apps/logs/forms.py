from django import forms


class SearchForm(forms.Form):
    q = forms.CharField(required=False, label="search",
            widget=forms.TextInput(attrs={'placeholder': 'Search'}))
