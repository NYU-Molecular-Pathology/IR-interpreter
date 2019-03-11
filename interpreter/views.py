from django.http import HttpResponse
from django.shortcuts import render
from .models import PMKBVariant
from .report import make_report_html
import subprocess

# try to get the app version from the git repo
version = None
try:
    version = subprocess.check_output(['git', 'describe', '--always']).decode('ascii').strip()
except:
    pass

MAX_UPLOAD_SIZE = 2 * 1024 * 1024 # 2MB

def index(request):
    """
    Returns the home page index
    """
    # get all the available tumor and tissue types to populate the uploads form
    all_tumor_types = sorted(PMKBVariant.objects.values_list('tumor_type', flat=True).distinct())
    all_tissue_types = sorted(PMKBVariant.objects.values_list('tissue_type', flat=True).distinct())
    template = "interpreter/index.html"
    context = {'version': version, 'tumor_types': all_tumor_types, 'tissue_types': all_tissue_types}
    return render(request, template, context)

def upload(request):
    """
    Responds to a POST request from an uploaded Ion Reporter .tsv file
    """
    if request.method == 'POST' and 'irtable' in request.FILES:
        # check for a tumor or tissue type passed
        tissue_type = request.POST.get('tissue_type', None)
        if tissue_type == 'None':
            tissue_type = None
        tumor_type = request.POST.get('tumor_type', None)
        if tumor_type == 'None':
            tumor_type = None

        # check for file too large
        if request.FILES['irtable'].size > MAX_UPLOAD_SIZE:
            return HttpResponse('Error: File is too large, size limit is: {0}MB'.format(MAX_UPLOAD_SIZE / (1024 * 1024)) )
        # check file type
        if not str(request.FILES['irtable']).endswith('.tsv'):
            return HttpResponse('Error: Invalid file type, filename must end with ".tsv"')

        # try to generate the HTML report
        try:
            report = make_report_html(input = request.FILES['irtable'],
                tissue_type = tissue_type,
                tumor_type = tumor_type)
            return HttpResponse(report)
        except:
            return HttpResponse('Error: File could not be parsed')
    else:
        return HttpResponse('Error: Invalid file selected')
