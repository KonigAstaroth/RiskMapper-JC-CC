from youdotcom import You
from django.conf import settings
from app.src.utils.report_generation_utils.lists import crimes_list_api

you_client = You(settings.YOU_API_KEY)

# This function deals with searching crimes in the API you, based on dates, crimes selected and place

def YouWebSearch(startDate_API, endDate_API, filtersAi, crimes_select):
    estado = filtersAi.get('Estado')
    municipio = filtersAi.get('Municipio')
    results_search =[]

    if not crimes_select:
        crimes_select = crimes_list_api 

    # For each item coming from a list in a checkbox input, it will search on the web
    for crime in crimes_select:
        str_query = f'{crime} AND {municipio} AND {estado}' #string formating for the query
        # API call
        search_results = you_client.search.unified(
            query= str_query,
            freshness= f'{startDate_API}to{endDate_API}',
            country = 'MX',
            count = 10
        )

        # Check if there is results
        if search_results.results and search_results.results.web:

            # Store resul data in the results list
            for result in search_results.results.web:
                snippets = result.snippets
                title = result.title

                if snippets and title:
                    texto = " ".join(snippets) if isinstance(snippets, list) else snippets
                    
                    results_search.append(
                        f"Titulo: {title}\n"
                        f"Delito: {crime}\n"
                        f"Texto: {texto}\n"
                    )
    
    return results_search
