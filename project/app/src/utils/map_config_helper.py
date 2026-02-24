
def map_config_center(request):
    map_config = request.session.get('map_config', {})
    if not map_config:
        map_config = {
        'center': {'lat': 19.42847, 'lng': -99.12766},
        'zoom': 6
    }
    return map_config