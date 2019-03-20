from django.http import HttpResponse
from django.shortcuts import render
from .models import PMKBVariant, UserAccessMetric, UserUploadMetric, TumorType, TissueType
from .report import make_report_html
import subprocess
import logging
from ipware import get_client_ip

# logger = logging.getLogger(__name__)
logger = logging.getLogger()

# try to get the app version from the git repo
version = None
try:
    version = subprocess.check_output(['git', 'describe', '--always']).decode('ascii').strip()
except:
    log.warning("could not get commit hash from git repo")
    pass

MAX_UPLOAD_SIZE = 2 * 1024 * 1024 # 2MB

def all_types(type, include_any = True):
    """
    Return a list of all types from the database
    """
    all_types = []
    if type == "tumor":
        all_types = sorted(TumorType.objects.values_list('type', flat = True).distinct())
    if type == "tissue":
        all_types = sorted(TissueType.objects.values_list('type', flat=True).distinct())
    if not include_any:
        all_types.remove('Any')
    return(all_types)

def index(request):
    """
    Returns the home page index
    """
    logger.info("index requested")
    ip, is_routable = get_client_ip(request)
    # save user access logging
    instance, created = UserAccessMetric.objects.get_or_create(ip = ip, view = 'index')

    # get all the available tumor and tissue types to populate the uploads form
    logger.debug("retrieving the available tumor and tissue types")
    # 'Any' is hard-coded as first entry in the HTML form
    all_tissue_types = all_types(type = "tissue", include_any = False)
    all_tumor_types = all_types(type = "tumor", include_any = False)

    # sanity check for initialized reference databses
    if len(all_tissue_types) < 1:
        logger.warn("all_tissue_types length is less than one; has the database been imported?")
    if len(all_tumor_types) < 1:
        logger.warn("all_tumor_types length is less than one; has the database been imported?")
    template = "interpreter/index.html"
    context = {'version': version, 'tumor_types': all_tumor_types, 'tissue_types': all_tissue_types}
    return render(request, template, context)

def upload(request):
    """
    Responds to a POST request from an uploaded Ion Reporter .tsv file
    """
    if request.method == 'POST' and 'irtable' in request.FILES:
        logger.info("POST requested")
        ip, is_routable = get_client_ip(request)
        instance, created = UserAccessMetric.objects.get_or_create(ip = ip, view = 'upload')
        # check for a tumor or tissue type passed
        # use 'Any' as the default value, pass as None-type to exclude filtering
        tissue_type = request.POST.get('tissue_type', 'Any')
        if tissue_type == 'Any':
            tissue_type = None
        tumor_type = request.POST.get('tumor_type', 'Any')
        if tumor_type == 'Any':
            tumor_type = None
        logger.debug("tissue_type: {tissue_type}, tumor_type: {tumor_type}".format(tumor_type = tumor_type, tissue_type = tissue_type))

        # check for file too large
        logger.debug("checking file size")
        if request.FILES['irtable'].size > MAX_UPLOAD_SIZE:
            logger.error("file size too large; {0:.2f}MB".format(request.FILES['irtable'].size / (1024 * 1024)))
            return HttpResponse('Error: File is too large, size limit is: {0}MB'.format(MAX_UPLOAD_SIZE / (1024 * 1024)) )
        # check file type
        logger.debug("checking file type")
        if not str(request.FILES['irtable']).endswith('.tsv'):
            logger.error("Invalid file type")
            return HttpResponse('Error: Invalid file type, filename must end with ".tsv"')

        instance, created = UserUploadMetric.objects.get_or_create(ip = ip, size = request.FILES['irtable'].size)

        # try to generate the HTML report
        try:
            logger.debug("generating report HTML")
            report = make_report_html(input = request.FILES['irtable'],
                tissue_type = tissue_type,
                tumor_type = tumor_type)
            return HttpResponse(report)
        except:
            logger.error("an error occured while generating report HTML")
            return HttpResponse('Error: An error occured while generating report HTML')
    else:
        return HttpResponse('Error: Invalid file selected')
