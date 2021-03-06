import requests
import datetime
from math import log10, floor
from typing import List
from copy import deepcopy


class ApiCaller:
    def __init__(self):

        # Caches
        self.country_list = []
        self.country_id_dict = {}
        self.population_cache = {}
        self.emissions_cache = {}
        self.population_year_cache = {}
        self.emissions_year_cache = {}

        # Generate a list of years from beginning of data (1960) to current year
        self.generic_year_list = []
        for x in range(1960, self.get_current_year() + 1):
            self.generic_year_list.append(x)

    country_url = "http://api.worldbank.org/v2/country/all?format=json&per_page=350"
    country_json = requests.get(country_url).json()
    generic_url = "http://api.worldbank.org/v2/en/country/"
    population_url = "/indicator/SP.POP.TOTL?format=json&per_page=500"
    emissions_url = "/indicator/EN.ATM.CO2E.KT?format=json&per_page=500"

    @staticmethod
    def get_current_year():
        current_datetime = datetime.datetime.now()
        return int(current_datetime.strftime("%Y"))

    def get_generic_year_list(self):
        return self.generic_year_list

    # Gets a list of years with available data for specific country and data type
    def get_year_list(self, country: str, data_type: str, year_min: int, year_max: int):
        if type(country) is not str:
            raise TypeError("country is expected to be of type str, got " + type(country).__name__)

        if type(data_type) is not str:
            raise TypeError("data_type is expected to be of type str, got " + type(data_type).__name__)

        if data_type != 'emissions' and data_type != 'population' and data_type != 'emissions_per_capita':
            raise ValueError("data_type must be 'emissions', 'population' or 'emissions_per_capita', got " + data_type)

        if type(year_min) is not int:
            raise TypeError("year_min is expected to be of type int, got " + type(year_min).__name__)

        if type(year_max) is not int:
            raise TypeError("year_min is expected to be of type int, got " + type(year_max).__name__)

        country_id = self.get_country_id(country)
        year_list = []

        # Reverses min and max if required
        if year_min > year_max:
            temp = year_max
            year_max = year_min
            year_min = temp

        def get_emissions_year_list():
            inner_year_list = []

            if country_id not in self.emissions_year_cache:
                emissions_list = (requests.get(self.generic_url + country_id + self.emissions_url)).json()

                for x in emissions_list[1]:  # [0] is metadata
                    if x['value'] is not None:
                        inner_year_list.insert(0, int(x['date']))

                self.emissions_year_cache[country_id] = inner_year_list

            elif country_id in self.emissions_year_cache:
                inner_year_list = self.emissions_year_cache[country_id]

            return inner_year_list

        def get_population_year_list():
            inner_year_list = []

            if country_id not in self.population_year_cache:
                population_list = (requests.get(self.generic_url + country_id + self.population_url)).json()

                for x in population_list[1]:  # [0] is metadata
                    if x['value'] is not None:
                        inner_year_list.insert(0, int(x['date']))

                self.population_year_cache[country_id] = inner_year_list

            elif country_id in self.population_year_cache:
                inner_year_list = self.population_year_cache[country_id]

            return inner_year_list

        if data_type == 'emissions':
            year_list = get_emissions_year_list()

        elif data_type == 'population':
            year_list = get_population_year_list()

        elif data_type == 'emissions_per_capita':
            year_list_1 = get_population_year_list()
            year_list_2 = get_emissions_year_list()

            # The intersection of both year lists
            year_list = list(set(year_list_1) & set(year_list_2))

        # The sorted intersection of the specified year range and the years with available data
        year_list = list(set(year_list) & set(range(year_min, year_max + 1)))
        year_list.sort()

        return year_list

    def get_country_list(self):
        if len(self.country_list) == 0:
            for country in self.country_json[1]:

                # Make sure not to include regions
                if country['region']['value'] != 'Aggregates':
                    self.country_list.append(country['name'])

        self.country_list = sorted(self.country_list)
        return self.country_list

    def get_country_id_dict(self):
        if len(self.country_id_dict) == 0:
            for country in self.country_json[1]:
                if country['region']['value'] != 'Aggregates':
                    self.country_id_dict[country['name']] = country['id'].lower()

        return self.country_id_dict

    def get_country_name_dict(self):
        country_dict = self.get_country_id_dict()
        inverted_dict = {}
        for key, value in country_dict.items():
            inverted_dict[value] = key

        return inverted_dict

    def get_country_id(self, country: str):
        if type(country) is not str:
            raise TypeError("country is expected to be of type str, got " + type(country).__name__)

        return self.get_country_id_dict()[country]

    def get_country_name(self, country_id: str):
        if type(country_id) is not str:
            raise TypeError("country_id is expected to be of type str, got " + type(country_id).__name__)

        return self.get_country_name_dict()[country_id]

    def get_data(self, country: str, data_type: str, year: int):
        if type(country) is not str:
            raise TypeError("country is expected to be of type str, got " + type(country).__name__)

        if type(data_type) is not str:
            raise TypeError("data_type is expected to be of type str, got " + type(data_type).__name__)

        if type(year) is not int:
            raise TypeError("year is expected to be of type int, got " + type(year).__name__)

        def get_population(inner_country_id: str, inner_year: int):
            if inner_country_id not in self.population_cache:
                population_list = requests.get(self.generic_url + inner_country_id + self.population_url).json()[1]
                self.population_cache[inner_country_id] = {}

                for population in population_list:
                    self.population_cache[inner_country_id][int(population['date'])] = population['value']

            return self.population_cache[inner_country_id][inner_year]

        def get_emissions(inner_country_id: str, inner_year: int):
            if inner_country_id not in self.emissions_cache:
                emissions_list = requests.get(self.generic_url + inner_country_id + self.emissions_url).json()[1]
                self.emissions_cache[inner_country_id] = {}

                for emissions in emissions_list:
                    self.emissions_cache[inner_country_id][int(emissions['date'])] = emissions['value']

            return self.emissions_cache[country_id][inner_year]

        def get_emissions_per_capita(inner_country_id: str, inner_year: int):
            value = (get_emissions(inner_country_id, inner_year) * 1000) / \
                    get_population(inner_country_id, inner_year)

            # Return number rounded to three significant figures

            return round(value, -int(floor(log10(abs(value)))) + 2)

        country_id = self.get_country_id(country)

        if data_type == 'emissions':
            return get_emissions(country_id, year)

        elif data_type == 'population':
            return get_population(country_id, year)

        elif data_type == 'emissions_per_capita':
            return get_emissions_per_capita(country_id, year)

        else:
            raise ValueError("data_type should be 'emissions', 'population', or 'emissions_per_capita', got"
                             + data_type)

    def get_data_range(self, country: str, data_type: str, year_min: int, year_max: int) -> dict:
        if type(country) is not str:
            raise TypeError("country is expected to be of type str, got " + type(country).__name__)

        if type(data_type) is not str:
            raise TypeError("data_type must be of type str, got " + type(data_type).__name__)

        if type(year_min) is not int:
            raise TypeError("year_min is expected to be of type int, got " + type(year_min).__name__)

        if type(year_max) is not int:
            raise TypeError("year_max is expected to be of type int, got " + type(year_max).__name__)

        if data_type != "emissions" and data_type != "population" and data_type != "emissions_per_capita":
            raise ValueError("data_type must be either 'emissions', 'population', or 'emissions_per_capita', got " +
                             data_type)

        year_range = self.get_year_list(country, data_type, year_min, year_max)
        data_range = {}

        for year in year_range:
            data_range[year] = self.get_data(country, data_type, year)

        return data_range

    def get_multiple_data_range(self, country_list: List[str], data_type: str, year_min: int, year_max: int):
        response = {}
        sorted_response = {}
        initial_year_dict = {}
        year_range = range(year_min, year_max + 1)
        for year in year_range:
            initial_year_dict[year] = None

        for country in country_list:
            country_data = self.get_data_range(country, data_type, year_min, year_max)
            response[country] = deepcopy(initial_year_dict)
            for year in response[country]:
                if year in country_data:
                    response[country][year] = country_data[year]

        for year in year_range:
            all_empty = True
            for country in response:
                if response[country][year] is not None:
                    all_empty = False
                    break

            if all_empty:
                for country in response:
                    response[country].pop(year, None)

        for item in sorted(response):
            sorted_response[item] = response[item]

        return sorted_response
