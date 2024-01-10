from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ColStressForm, ColSanteForm
from .models import ColSante, ColStress
from authentification.models import Utilisateur, medecinPatient
from datetime import datetime, date, timedelta
from django.db.utils import OperationalError
import pandas as pd
from .mlflow_utils import init_mlflow, send_alert_discord
import mlflow
import sqlite3
from django.db import connection, connections
import random
from django.http import HttpResponseBadRequest
import numpy as np

init_mlflow()

# Connexion à la base de données SQLite
conn = sqlite3.connect('mlflow.db')
cursor = conn.cursor()
# Définir le seuil d'alerte
SEUIL_ALERT = 3
# Exécution de la requête SQL pour récupérer les x dernières valeurs
cursor.execute(f'SELECT value FROM metrics ORDER BY timestamp DESC')
values = cursor.fetchall()
x_last_values = values[-SEUIL_ALERT:]
x_all_zero = all(value == 0 for value in x_last_values)
# Fermeture de la connexion à la base de données
conn.close()

# Create your views here.
def handle_form_submission(form, form_name):
    global SEUIL_ALERT
    global values
    global x_all_zero


    with connections['default'].cursor() as cursor:
        x = random.randint(1, 100)
        print("est le numéro gagnant est le", x, flush=True)
        if (x % 2) == 0:
            print("pas de chance, ça va être tout noir", flush=True)
            cursor.connection.close()
            #if cursor.connection.closed:
                #print("connexion interrompue", flush=True)
    try:
        form.save()
        mlflow.log_metric("insertions_successful", 1)

    except Exception as e:
        # Enregistrez un événement MLflow pour le suivi des erreurs
        mlflow.log_metric("insertions_successful", 0)
        mlflow.log_param("error_message", f"{form_name}: {str(e)}")

        if len(values) >= SEUIL_ALERT:
            if x_all_zero:
                print('seuil atteint', flush=True)
                send_alert_discord("Alerte MLflow", f"Le seuil d'échecs consécutifs ({SEUIL_ALERT}) a été atteint.")



@login_required
def accueil(request):
    prenom = request.user.username
    return render(request,
                  "accueil.html",
                  context={"prenom": prenom})

@login_required
def data_stress(request, prochainFormulaire_date_stress=None):
    message = ""
    svp = ""
    disabled = ""
    #connection = connections['default']

    try:
        dateDernierFormulaireDuPatient = list(ColStress.objects.filter(user_id=Utilisateur.objects.filter(username=request.user.username)[0]))[-1].date
        dateDernierFormulaireDuPatient = datetime.strptime(dateDernierFormulaireDuPatient, '%d/%m/%Y')

        try:
            medecinTraitant = medecinPatient.objects.filter(idPatient=Utilisateur.objects.filter(username=request.user.username)[0].id)[0].idMedecin
            periodiciteForm = Utilisateur.objects.filter(username=medecinTraitant)[0].periodiciteStress
        except:
            periodiciteForm = Utilisateur.objects.filter(username=request.user.username)[0].periodiciteStress

        prochainFormulaire = dateDernierFormulaireDuPatient + timedelta(days=periodiciteForm)
        prochainFormulaire = prochainFormulaire.strftime('%d/%m/%Y')

        # Convert prochainFormulaire_str back to datetime.date
        prochainFormulaire_date_stress = datetime.strptime(prochainFormulaire, '%d/%m/%Y').date()
        remplirProchainFormulaire = datetime.now().date() > prochainFormulaire_date_stress
    except:
        remplirProchainFormulaire = True
        periodiciteForm = Utilisateur.objects.filter(username=request.user.username)[0].periodiciteStress
        svp = "Veuillez remplir votre premier formulaire"

    if request.user.role != "patient":
        return redirect("accueil")
    else:
        prenom = request.user.username
        initial_data = {'prénom': prenom}
        initial_data['date'] = date.today().strftime('%d/%m/%Y')

        if request.method == 'POST':
            form = ColStressForm(request.POST, initial=initial_data)
            if form.is_valid() and remplirProchainFormulaire:
                handle_form_submission(form, "data_stress")
                return redirect('accueil')  # Redirect to a confirmation page
            elif not remplirProchainFormulaire:
                message = "Vous ne pouvez pas encore soumettre de réponse pour ce questionnaire"
        else:
            form = ColStressForm(initial=initial_data)

    return render(
        request,
        'data_stress.html',
        {'form': form, 'prochainFormulaire_date_stress': prochainFormulaire_date_stress, 'message': message, 'periodiciteForm': periodiciteForm, 'svp': svp,'remplirProchainFormulaire': remplirProchainFormulaire}
    )



@login_required
def data_sante(request, prochainFormulaire_date_sante=None):
    message = ""
    svp = ""
    disabled = ""

    try:
        dateDernierFormulaireDuPatient = list(ColSante.objects.filter(user_id=Utilisateur.objects.filter(username=request.user.username)[0]))[-1].date
        dateDernierFormulaireDuPatient = datetime.strptime(dateDernierFormulaireDuPatient, '%d/%m/%Y')

        try:
            medecinTraitant = medecinPatient.objects.filter(idPatient=Utilisateur.objects.filter(username=request.user.username)[0].id)[0].idMedecin
            periodiciteForm = Utilisateur.objects.filter(username=medecinTraitant)[0].periodiciteSante
        except:
            periodiciteForm = Utilisateur.objects.filter(username=request.user.username)[0].periodiciteSante

        prochainFormulaire = dateDernierFormulaireDuPatient + timedelta(days=periodiciteForm)
        prochainFormulaire = prochainFormulaire.strftime('%d/%m/%Y')

        # Convert prochainFormulaire_str back to datetime.date
        prochainFormulaire_date_sante = datetime.strptime(prochainFormulaire, '%d/%m/%Y').date()
        remplirProchainFormulaire = datetime.now().date() > prochainFormulaire_date_sante
    except:
        remplirProchainFormulaire = True
        periodiciteForm = Utilisateur.objects.filter(username=request.user.username)[0].periodiciteSante
        svp = "Veuillez remplir votre premier formulaire"

    if request.user.role != "patient":
        return redirect("accueil")
    else:
        prenom = request.user.username
        initial_data = {'prénom': prenom}
        initial_data['date'] = date.today().strftime('%d/%m/%Y')

        if request.method == 'POST':
            form = ColSanteForm(request.POST, initial=initial_data)
            if form.is_valid() and remplirProchainFormulaire:
                handle_form_submission(form, "data_sante")
                return redirect('accueil')  # Redirect to a confirmation page
            elif not remplirProchainFormulaire:
                message = "Vous ne pouvez pas encore soumettre de réponse pour ce questionnaire"
        else:
            form = ColSanteForm(initial=initial_data)

    return render(
        request,
        'data_sante.html',
        {'form': form, 'prochainFormulaire_date_sante': prochainFormulaire_date_sante, 'message': message, 'periodiciteForm': periodiciteForm, 'svp': svp,'remplirProchainFormulaire': remplirProchainFormulaire}
    )


#interdire accès à une page en fonction du rôle
'''if request.user.role != "medecin":
    return redirect ("accueil") #ou autre page disant que fais-tu là
else:
    return render (request, "page en question")'''

@login_required
def stress_datatable(request):
    user = request.user
    pat = []

    if request.method == "POST":
        periodiciteStress = request.POST.get("periodiciteStress")

        # Update periodicity for the connected user
        Utilisateur.objects.filter(id=user.id).update(
            periodiciteStress=periodiciteStress
        )

    # Fetch updated periodicity values
    user.refresh_from_db()
    periodiciteStress = user.periodiciteStress

    if user.role == "responsable":
        idDesFormulaires = [valeur.id for valeur in ColStress.objects.all()]
        dataFormulaireStress = [ColStress.objects.filter(id=id).values()[0].values() for id in idDesFormulaires]
    elif user.role == "medecin":
        for p in medecinPatient.objects.filter(idMedecin=user.id).values():
            username_pat = Utilisateur.objects.get(id=p["idPatient_id"]).username
            dataFormulaireStress = [el.values() for el in ColStress.objects.filter(user_id=username_pat).values()]
            pat.extend(dataFormulaireStress)

    champsFormulaireStress = [field.name for field in ColStress._meta.get_fields()]

    return render(request, "stress_datatable.html", {
        "dataFormulaireStress": pat if user.role == "medecin" else dataFormulaireStress,
        "champsFormulaireStress": champsFormulaireStress,
        "periodiciteStress": periodiciteStress
    })



@login_required
def sante_datatable(request):
    user = request.user
    pat = []

    if request.method == "POST":
        periodiciteSante = request.POST.get("periodiciteSante")

        # Update periodicity for the connected user
        Utilisateur.objects.filter(id=user.id).update(
            periodiciteSante=periodiciteSante
        )

    # Fetch updated periodicity values
    user.refresh_from_db()
    periodiciteSante = user.periodiciteSante

    if user.role == "responsable":
        #idDesFormulaires = [valeur.id for valeur in ColSante.objects.all()]
        #dataFormulaireSante = [ColSante.objects.filter(id=id).values()[0].values() for id in idDesFormulaires]
        dataFormulaireSante = [ColSante.objects.filter(id=valeur.id).values()[0].values() for valeur in ColSante.objects.all()]

    elif user.role == "medecin":
        for p in medecinPatient.objects.filter(idMedecin=user.id).values():
            username_pat = Utilisateur.objects.get(id=p["idPatient_id"]).username
            dataFormulaireSante = [el.values() for el in ColSante.objects.filter(user_id=username_pat).values()]
            pat.extend(dataFormulaireSante)

    champsFormulaireSante = [field.name for field in ColSante._meta.get_fields()]

    return render(request, "sante_datatable.html", {
        "dataFormulaireSante": pat if user.role == "medecin" else dataFormulaireSante,
        "champsFormulaireSante": champsFormulaireSante,
        "periodiciteSante": periodiciteSante
    })

@login_required
def association(request):
    prenom = request.user.username
    if request.user.role == "patient":
        return redirect ("accueil") #ou autre page disant que fais-tu là
    else:
    #return render (request, "page en question")
    # 1- Récupérer la liste des id des médecins et des patients
    # 2- Ensuite on ne garde que les patients qui ne sont pas dans la table medecinPatient
    # 3- On créé ensuite un template qui contiendra une liste déroulante
    # 4- Dans cette liste déroulante on va afficher d'un côté les médecins
    # et de l'autre les patients filtrés (voir étapge 2)
    # https://developer.mozilla.org/fr/docs/Web/HTML/Element/select
        medecinsID = [medecin for medecin in Utilisateur.objects.filter(role="medecin")]
        patientsID = [patient for patient in Utilisateur.objects.filter(role="patient")]
        listePatientsAssocies = [ligne.idPatient for ligne in medecinPatient.objects.all()]
        listePatientsNonAssocies = [id for id in patientsID if id not in listePatientsAssocies]
        tableAssociation = medecinPatient.objects.all()
        # Syntaxe équivalente
        # for id in patientsID :
        #    if id not in listePatientsAssocies:
        #        patientsNonAssocies.append(id)
        if request.method == "POST":
            medecin_username = request.POST["medecin"]
            patient_username = request.POST["patient"]
            medecin = Utilisateur.objects.get(username=medecin_username)
            patient = Utilisateur.objects.get(username=patient_username)
            print("medecin", type(medecin), medecin)
            medecinPatient(idMedecin=medecin, idPatient=patient).save()
            return redirect("association")
        return render(request, "association.html",
                      {"listePatientsNonAssocies": listePatientsNonAssocies,
                       "medecinsID": medecinsID,
                       "tableAssociation" : tableAssociation, "prenom": prenom})

@login_required
def histo_patient(request):
    champsFormulaireStress = [field.name for field in ColStress._meta.get_fields()]
#    idDesFormulairesStr = [valeur.id for valeur in ColStress.objects.all()]
    idDesFormulairesStr = [valeur.id for valeur in ColStress.objects.filter(user_id=request.user.username)]
    dataFormulaireStress = [ColStress.objects.filter(id=id).values()[0].values() for id in idDesFormulairesStr]

    champsFormulaireSante = [field.name for field in ColSante._meta.get_fields()]
#    idDesFormulairesSante = [valeur.id for valeur in ColSante.objects.all()]
    idDesFormulairesSante = [valeur.id for valeur in ColSante.objects.filter(user_id=request.user.username)]

    dataFormulaireSante = [ColSante.objects.filter(user_id=request.user.username).values()[0].values() for id in idDesFormulairesSante]
    return render(request, "histo_patient.html",
                  {"dataFormulaireSante" : dataFormulaireSante,
                   "champsFormulaireSante" : champsFormulaireSante,
                  "dataFormulaireStress" : dataFormulaireStress,
                   "champsFormulaireStress" : champsFormulaireStress})


@login_required
def edaia(request):
    # URL de l'image externe
    image_url = "https://upload.wikimedia.org/wikipedia/commons/1/19/Under_construction_graphic.gif"
    # Passer l'URL à la template
    context = {
        'image_url': image_url,
    }
    return render(request, 'edaia.html', context)


#print(list(utilisateur.username for utilisateur in Utilisateur.objects.filter(role="medecin")))


def alimentationPatients():
    listePatients = pd.read_csv("https://raw.githubusercontent.com/data-IA-2022/Doctolib-_-Maud/main/data/listepat.csv")
    for index, valeurs in listePatients.iterrows():
        #champDBB = Utilisateur._meta.get_fields()

        Utilisateur.objects.create_user(username = valeurs.username,
                                        password = valeurs.password,
                                        role="patient")
def alimentationMedecin():
    listeMedecins = pd.read_csv("https://raw.githubusercontent.com/data-IA-2022/Doctolib-_-Maud/main/data/listemed.csv")
    for index, valeurs in listeMedecins.iterrows():
        Utilisateur.objects.create_user(username = valeurs.username,
                                        password = valeurs.password,
                                        role="medecin")

def modifier_role_superutilisateur():
    # Cherche tous les superutilisateurs
    superusers = Utilisateur.objects.filter(is_superuser=True)

    # Modifie le rôle du superutilisateur en 'responsable'
    for superuser in superusers:
        superuser.role = 'responsable'
        superuser.save()

try:
    modifier_role_superutilisateur()
except OperationalError as e:
    print(e)

try:
    if len(Utilisateur.objects.filter(role="patient")) == 0:
        alimentationPatients()
    if len(Utilisateur.objects.filter(role="medecin")) == 0:
        alimentationMedecin()
except OperationalError as e:
    print(e)
