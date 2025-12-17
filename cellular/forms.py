from django import forms
from .choices import DatasetSource


class CellTowerImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Cell towers csv File",
        help_text="Upload a CSV file containing cell tower data(mcc, mnc, cell_id, lat, lon).",
    )
    dataset_source = forms.ChoiceField(
        label="Dataset source",
        choices=DatasetSource.choices,
        initial=DatasetSource.OTHER,
        help_text="Choose the source of this dataset (e.g., MLS, OpenCellID).",
    )
    update_existing = forms.BooleanField(
        label="Update existing records",
        required=False,
        initial=True,
        help_text="if checked, existing cell tower records will be updated with new data from the CSV file.",
    )
