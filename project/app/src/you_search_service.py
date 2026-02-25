from youdotcom import You
from django.conf import settings
from app.src.utils.report_generation_utils.lists import crimes_list_api
import asyncio
from functools import partial

you_client = You(settings.YOU_API_KEY)

# This function deals with searching crimes in the API you, based on dates, crimes selected and place
async def YouWebSearch(startDate_API, endDate_API, filtersAi, crimes_select):

    estado = filtersAi.get('Estado')
    municipio = filtersAi.get('Municipio')
    results_search = []

    if not crimes_select:
        crimes_select = crimes_list_api

    loop = asyncio.get_running_loop()

    async def search_crime(crime):

        str_query = f'{crime}'
        if estado:
            str_query += f' AND {estado}'
        if municipio:
            str_query += f' AND {municipio}'

        search_func = partial(
            you_client.search.unified,
            query=str_query,
            freshness=f'{startDate_API}to{endDate_API}',
            country='MX',
            count=10
        )

        search_results = await loop.run_in_executor(None, search_func)

        crime_results = []

        if search_results.results and search_results.results.web:
            for result in search_results.results.web:
                snippets = result.snippets
                title = result.title

                if snippets and title:
                    texto = " ".join(snippets) if isinstance(snippets, list) else snippets

                    crime_results.append(
                        f"Titulo: {title}\n"
                        f"Delito: {crime}\n"
                        f"Texto: {texto}\n"
                    )

        return crime_results

    tareas = [search_crime(crime) for crime in crimes_select]
    resultados = await asyncio.gather(*tareas)

    for r in resultados:
        results_search.extend(r)

    return results_search
