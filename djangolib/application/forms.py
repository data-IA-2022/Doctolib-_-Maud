from django import forms
from django.db import models
from .models import ColStress, ColSante


class BooleanSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        choices = [
            ('', '---------'),
            ('True', 'Oui'),
            ('False', 'Non'),
        ]
        super().__init__(*args, **kwargs)
        self.choices = self.choices + choices

class ColStressForm(forms.ModelForm):
    class Meta:
        model = ColStress
        exclude = ['total_de_limpact_du_stress_dans_votre_vie_actuelle']

    def __init__(self, *args, **kwargs):
        super(ColStressForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial', {})
        if 'prénom' in initial:
            self.initial['user_id'] = initial['prénom']


class ColSanteForm(forms.ModelForm):
    class Meta:
        model = ColSante
        fields = '__all__'

        widgets = {
            field.name: forms.NumberInput(attrs={'min': 0})
            for field in ColSante._meta.get_fields()
            if isinstance(field, (forms.IntegerField, models.IntegerField)) and field.name != 'id'
        }

    def __init__(self, *args, **kwargs):
        super(ColSanteForm, self).__init__(*args, **kwargs)

        text_widgets = [
            'tour_de_taille_en_cm', 'poids', 'fréquence_cardiaque_par_minute',
            'tension_artérielle_systolique_prise_du_matin', 'tension_artérielle_systolique_prise_du_soir',
            'tension_artérielle_diastolique_prise_du_matin', 'tension_artérielle_diastolique_prise_du_soir',
            'nombre_de_médicaments_pris_dans_la_journée', 'nombre_de_repas_pris_durant_la_journée',
            'durée_de_lactivité_physique_en_minutes', 'durée_totale_des_palpitations_en_minutes',
            'durée_totale_des_douleurs_thoraciques_en_minutes', 'durée_totale_des_malaises_en_minutes',
        ]

        for field_name in text_widgets:
            self.fields[field_name].widget = forms.TextInput(attrs={'type': 'text', 'data-integerfield': 'true'})

        boolean_fields = [
            'oubli_de_prendre_les_médicaments_le_matin', 'oubli_de_prendre_les_médicaments_le_soir',
            'effets_secondaires_remarqués', 'symptomes_particuliers_remarqués', 'consommation_dalcool',
            'grignotage_sucre', 'grignotage_sale', 'activité_physique_aujourdhui', 'présence_de_dyspnée',
            'présence_dœdème', 'présence_dépisode_infectieux', 'présence_de_fièvre',
            'présence_de_palpitation', 'présence_de_douleur_thoracique', 'présence_de_malaise',
        ]

        for field_name in boolean_fields:
            # Ajoutez le widget à la liste existante des widgets
            self.fields[field_name].widget = BooleanSelect()

        initial = kwargs.get('initial', {})
        if 'prénom' in initial:
            self.initial['user_id'] = initial['prénom']
