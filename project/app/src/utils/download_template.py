from django.http import FileResponse
from django.conf import settings
import os


def downloadTemplate(request):
    file_path = os.path.join(settings.BASE_DIR, 'app', 'xlsx_templates', 'template_cerberus_final.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))