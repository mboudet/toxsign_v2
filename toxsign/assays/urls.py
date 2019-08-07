from django.urls import path
from toxsign.assays import views

app_name = "assays"
urlpatterns = [
    path('create/assay/<str:prjid>', views.CreateAssayView.as_view(), name='assay_create'),
    path('create/factor/<str:prjid>', views.CreateFactorView.as_view(), name='factor_create'),
    path('factor/<str:facid>/', views.DetailFactorView, name='factor_detail'),
    path('assay/<str:assid>/', views.DetailAssayView, name='assay_detail'),
    path('edit/assay/<str:assid>/', views.EditAssayView.as_view(), name='assay_edit'),
    path('edit/factor/<str:facid>/', views.EditFactorView.as_view(), name='factor_edit'),
]
