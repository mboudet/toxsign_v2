# Generated by Django 2.0.13 on 2019-10-08 08:31

from django.db import migrations

import sys
import os
import tempfile
import shutil
from urllib.request import urlopen
from zipfile import ZipFile
import gzip
from time import gmtime, strftime
from toxsign.genes.models import Gene

def download_datafiles():

    dirpath = '/app/loading_data/genes/'
    urls = ["ftp://ftp.ncbi.nih.gov/gene/DATA/gene2ensembl.gz","ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz","ftp://ftp.ncbi.nih.gov/pub/HomoloGene/build68/homologene.data"]
    for url in urls :
        if not check_file(dirpath, url):
            file_name = url.split('/')[-1]
            u = urlopen(url)
            f = open(os.path.join(dirpath,file_name), 'wb')
            meta = u.info()
            file_size = int(meta.get("Content-Length")[0])
            print("Downloading: %s"% (file_name))

            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                f.write(buffer)

            f.close()
            if ".gz" in file_name :
                with gzip.open(os.path.join(dirpath,file_name), 'rb') as f_in:
                    with open(os.path.join(dirpath,file_name.replace('.gz','')), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

    return dirpath

def concat_files(dirpath, use_dl=False, file_list=[]):

    gene2ensembl = gene_info = homologene = ""
    lTaxID=["9606","9598","9544","9615","9913","10090","10116","9031","8364","7955","7227","7165","6239","4932","28985","33169","4896","318829","5141","3702","4530"]

    if use_dl not in (True,False):
        raise ValueError("'use_dl' can only be either True or False")
    try :
        if use_dl :
            gene2ensembl = os.path.join(dirpath,'gene2ensembl')
            gene_info = os.path.join(dirpath,'gene_info')
            homologene = os.path.join(dirpath,'homologene.data')
        elif len(file_list) == 3 :
            gene2ensembl = file_list[0]
            gene_info = file_list[1]
            homologene = file_list[2]
        else:
            return "ERROR - Not enougth files provided"

    except IOError as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("filename: ", e.filename)
        print("strerror: ", e.strerror)

    dData_organized = {}
    # Init dico with gene_info file
    print("INDEX gene_info")
    try :
        print(gene_info)
        fGene_info = open(gene_info,'r')
        for gene_ligne in fGene_info.readlines():
            if gene_ligne[0] != '#':
                line_split = gene_ligne.split('\t')
                tax_id = line_split[0]
                GeneID = line_split[1]
                symbol = line_split[2]
                synonyms = line_split[4]
                description = line_split[8]
                if tax_id in lTaxID :
                    if GeneID not in dData_organized :
                        dData_organized[GeneID] = {'tax_id':tax_id,'symbol':symbol,'synonyms':synonyms,'description':description,'homologene':'NA','ensembl':'NA'}
        fGene_info.close()
    except Exception as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("strerror: ", e.strerror)

    #Add Ensembl ID informations
    print("INDEX gene2ensembl")
    try :
        fgene2ensembl = open(gene2ensembl,'r')
        for geneensemble_ligne in fgene2ensembl.readlines():
            if geneensemble_ligne[0] != '#':
                line_split = geneensemble_ligne.split('\t')
                tax_id = line_split[0]
                GeneID = line_split[1]
                ensemblID = line_split[2]
                if GeneID in dData_organized :
                    dData_organized[GeneID]['ensembl'] = ensemblID

        fgene2ensembl.close()
    except IOError as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("filename: ", e.filename)
        print("strerror: ", e.strerror)

    #Add Homologenes ID informations
    print("INDEX homologene")
    try :
        fhomologene = open(homologene,'r')
        for genehomo_ligne in fhomologene.readlines():
            if genehomo_ligne[0] != '#':
                line_split = genehomo_ligne.split('\t')
                tax_id = line_split[1]
                GeneID = line_split[2]
                homologeID = line_split[0]
                symbol = line_split[3]
                if GeneID in dData_organized :
                    if dData_organized[GeneID]['tax_id'] == tax_id :
                        dData_organized[GeneID]['homologene'] = homologeID

        fhomologene.close()

    except IOError as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("filename: ", e.filename)
        print("strerror: ", e.strerror)

    print("Writing file")
    try :
        resultFile = open(os.path.join(dirpath,'RGV_database_genes.txt'),'a')
        for geneID in dData_organized:
            resultFile.write(geneID+'\t'+dData_organized[geneID]['tax_id']+'\t'+dData_organized[geneID]['homologene']+'\t'+dData_organized[geneID]['ensembl']+'\t'+dData_organized[geneID]['symbol']+'\t'+dData_organized[geneID]['synonyms']+'\t'+dData_organized[geneID]['description']+'\n')
        resultFile.close()
        return [dirpath,os.path.join(dirpath,'RGV_database_genes.txt')]
    except IOError as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("filename: ", e.filename)
        print("strerror: ", e.strerror)

def insertCollections(genefile):
    try :
        print('CreateCollection - create RGV_geneDB collection')
        #Insert Allbank ID from TOXsIgN_geneDB file
        geneFile = open(genefile[1],'r')
        geneList = []

        for geneLine in geneFile.readlines():
            if geneLine[0] != '#':
                split = geneLine.split('\t')
                GeneID = split[0]
                tax_id = split[1]
                homologeneID = split[2]
                ensembleID = split[3]
                Symbol = split[4]
                Synonyms = split[5]
                description = split[6]
                geneList.append(Gene(gene_id=GeneID, tax_id=tax_id, homolog_id=homologeneID, ensembl_id=ensembleID, symbol=Symbol, synonyms=Synonyms, description=description))
        Gene.objects.bulk_create(geneList)
        geneFile.close()
        print("File close")

    except IOError as e:
        print("args: ", e.args)
        print("errno: ", e.errno)
        print("filename: ", e.filename)
        print("strerror: ", e.strerror)

def check_file(path, url):

        file_name = url.split('/')[-1]
        if ".gz" in file_name :
            file_name = file_name.replace('.gz','')

        return os.path.exists(os.path.join(path, file_name))

def setup(apps, schema_editor):
    # Do not populate in testing environment
    if os.environ.get("MODE") == "TEST":
        return

    dirpath = download_datafiles()
    gene_file = concat_files(dirpath, use_dl=True)
    insertCollections(gene_file)

class Migration(migrations.Migration):

    dependencies = [
        ('genes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(setup)
    ]
