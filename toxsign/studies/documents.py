from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from toxsign.studies.models import Study
from toxsign.projects.models import Project
from toxsign.assays.models import Assay

@registry.register_document
class StudyDocument(Document):

    project = fields.ObjectField(properties={
        'id': fields.TextField()
    })

    created_by = fields.ObjectField(properties={
        'username': fields.TextField()
    })

    class Index:
        # Name of the Elasticsearch index
        name = 'studies'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Study # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'name',
            'tsx_id',
            'created_at',
            'description',
            'experimental_design',
        ]
        related_models = [Project]
        ignore_signals = False

    def get_queryset(self):
        """Not mandatory but to improve performance we can select related in one sql request"""
        return super(StudyDocument, self).get_queryset().select_related(
            'project',
        )

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, Project):
            return related_instance.study_of.all()
