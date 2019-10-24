# Generated by Django 2.0.13 on 2019-07-02 09:37

from django.db import migrations
from django_elasticsearch_dsl.registries import registry
import toxsign.ontologies.models as onto_models

import traceback
import csv
import pronto
import os
import requests
import time
from multiprocessing import Process, Lock

ontology_models = {
    'biological': 'Biological',
    'cellline': 'CellLine',
    'cell': 'Cell',
    'chemical': 'Chemical',
    'disease': 'Disease',
    'experiment': 'Experiment',
    'species': 'Species',
    'tissue': 'Tissue'
}

def get_children_loop(ontology):
    visited = set()
    nonvisited = set()
    nonvisited.update(ontology.children)
    while nonvisited:
        item = nonvisited.pop()
        # already seen
        if item.id in visited:
            continue
        # mark item
        visited.add(item.id)
        # add children
        nonvisited.update(item.children)
    return visited

def temp_process(ontology, model):

    id = ontology.id
    name = ontology.name if ontology.name else ontology.id
    synonyms = ",".join([synonym.desc for synonym in ontology.synonyms]) if ontology.synonyms else ""
    children = ",".join(get_children_loop(ontology))

    return model(onto_id=id, name=name, as_children=children)

def temp_download_ontology(onto, lock):
    url = onto['url']
    path = onto['path']
    model = onto['model']
    location = onto['location']

    if location == "remote" and not os.path.exists(path):
        if url:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
    lock.acquire()
    if not os.path.exists(path):
        if location == "local":
            print("Error : local file not found at path " + path)
            print("Skipping")
        else:
            print("Error : remote file was not downloaded at path " + path)
            print("Skipping")
        lock.release()
        return
    try:
        print("Processing onto " + path)
        processed = []
        start = time.time()
        ontologies = pronto.Ontology(path)
        for ontology in ontologies:
            processed.append(temp_process(ontology, model))
        model.objects.bulk_create(processed)
        end = time.time()
        print("Time:")
        print(end - start)
        print(len(ontologies) - len(processed))
    except Exception as e:
        print(e)
        raise e
    finally:
        lock.release()

def launch_import(apps, schema_editor):
    # Do not populate in testing environment
    if os.environ.get("MODE") == "TEST":
        print("Testing environment, skipping ontologies loading")
        return

    if not os.path.exists("/app/loading_data/ontologies/TOXsIgN_ontologies.csv"):
        print("Not TOXsIgN_ontologies.csv file found. Skipping...")

    start = time.time()
    # Maybe a lock for each table insead of just one?
    lock = Lock()
    url_list = []
    with open('/app/loading_data/ontologies/TOXsIgN_ontologies.csv', 'r') as line:
        next(line)
        tsv = csv.reader(line)
        for row in tsv:
            if not len(row) == 6:
                print("Malformed row : incorrect argument number : " + len(tsv))
                continue
            if row[3] == 'owl' or row[3] == 'obo':
                model = apps.get_model('ontologies', ontology_models[row[2]])
                url_list.append({"url": row[1], "path": row[4], "model": model, "location": row[5]})
    procs = []
    for onto in url_list:
        p = Process(target=temp_download_ontology, args=(onto, lock))
        p.start()
        procs.append(p)

    for proc in procs:
        proc.join()
    for index in registry.get_indices():
        if index.exists():
            index.delete()
        index.create()
        # Populate indexes
    for doc in registry.get_documents():
        qs = doc().get_queryset()
        doc().update(qs)

    stop = time.time()
    print(stop-start)

class Migration(migrations.Migration):

    dependencies = [
        ('ontologies', '0007_auto_20190913_0724'),
        ('signatures', '0006_signature_expression_values_file'),
        ('assays', '0006_remove_assay_status'),
        ('projects', '0007_auto_20190905_1324'),
    ]

    operations = [
	    #migrations.RunPython(launch_import),
    ]
