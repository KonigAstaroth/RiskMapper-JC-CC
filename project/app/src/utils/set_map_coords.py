from django.shortcuts import redirect
from app.src.utils.getCoords import getLatLng


def setSearchCoords(request):
    if request.method == 'POST':
        location_input = request.POST.get('search-input')
        coords = getLatLng(location_input)
        request.session['map_config'] = coords
    return redirect('main')