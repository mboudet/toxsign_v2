# Generated by Django 2.0.13 on 2019-08-13 08:52


from django.core.management.base import BaseCommand, CommandError
from django.db import migrations
from django.core.files import File
from toxsign.tools.models import PredictionModel
from datetime import datetime
import os, shutil

# Populate with default tools (ontologies..)

def populate_prediction_models(folder):

    if not os.path.exists(folder):
        print("Folder {} does not exists. Exiting.".format(folder))
        return

    if not os.path.exists("/app/toxsign/media/jobs/admin/mat_chempsy_final_10793.tsv"):
        if not os.path.exists(os.path.join(folder, "mat_chempsy_final_10793.tsv")):
            print("Chempsy matrix not setup and not found in folder. Stopping.")
            return
        else:
            shutil.copy2(os.path.join(folder, "mat_chempsy_final_10793.tsv"), "/app/toxsign/media/jobs/admin/mat_chempsy_final_10793.tsv")

    if not (os.path.exists(os.path.join(folder, "association_matrix_cor.tsv")) and os.path.exists(os.path.join(folder, "model_cor.h5"))):
        print("Missing either {} or {}. Stopping.".format("association_matrix_cor.tsv", "model_cor.h5"))
        return

    if not (os.path.exists(os.path.join(folder, "association_matrix_euc.tsv")) and os.path.exists(os.path.join(folder, "model_euc.h5"))):
        print("Missing either {} or {}. Stopping.".format("association_matrix_euc.tsv", "model_euc.h5"))
        return

    description="This model return the probability that the chemical(s) related to a signature is part of a <a href='https://www.anses.fr/fr/content/chempsy-identification-classification-and-prioritization-novel-endocrine-disruptors'>ChemPSy</a> defined cluster."
    corr_description = description + "<br>This model will return clusters defined using correlation as similar proximity</br>"
    eucl_description = description + "<br>This model will return clusters defined using euclidean distance as similar proximity</br>"

    correlation_model = PredictionModel(
        name="ChemPSy cluster prediction (correlation)",
        computer_name="correlation",
        description=corr_description,
        parameters={"cluster_distance_type":"correlation"}
    )

    correlation_model.model_file.save("Ontology.svg", File(open(os.path.join(folder, "model_cor.h5"), "rb")), save=False)
    correlation_model.association_matrix.save("Ontology.svg", File(open(os.path.join(folder, "association_matrix_cor.tsv"), "rb")), save=False)
    correlation_model.save()

    euclidean_model = PredictionModel(
        name="ChemPSy cluster prediction (euclidean)",
        computer_name="euclidean",
        description=eucl_description,
        parameters={"cluster_distance_type":"euclidean"}
    )

    euclidean_model.model_file.save("Ontology.svg", File(open(os.path.join(folder, "model_euc.h5"), "rb")), save=False)
    euclidean_model.association_matrix.save("Ontology.svg", File(open(os.path.join(folder, "association_matrix_euc.tsv"), "rb")), save=False)
    euclidean_model.save()


class Command(BaseCommand):

    help = 'Load prediction models'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('data_folder', type=str, help='Folder containing the files. Must contain ')

    def handle(self, *args, **options):
        # Cleanup to avoid duplicate in tools images
        populate_prediction_models(options['data_folder'])
