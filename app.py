from flask import Flask, render_template, request, jsonify
from apiCaller import ApiCaller

app = Flask(__name__)

api_caller = ApiCaller()


# Returns a color based on the hash of the country name
def get_color(name: str):

    # Gets a 9 digit hash from provided string as a string
    name_hash = str(hash(name) % 10 ** 9)

    # Converts 3 digit decimal integer to a decimal int between 0 and 255
    def to_hex(num):
        return str(int((num/999)*255))

    r = to_hex(int(name_hash[0:3]))
    b = to_hex(int(name_hash[3:6]))
    g = to_hex(int(name_hash[6:9]))

    return "rgb(" + r + "," + g + "," + b + ')'


@app.route('/', methods=["POST", "GET"])
def index():
    generic_country_list = api_caller.get_country_list()
    generic_year_list = api_caller.get_generic_year_list()

    current_year = ApiCaller().get_current_year()

    year_min = int(1960)
    year_max = ApiCaller().get_current_year()

    data_type = None
    labels = generic_year_list
    values = []
    input_country_list = []
    country_amount = 0
    color_list = []

    is_empty = False
    received = False
    invalid = False

    if request.method == "POST":
        received = True

        input_country_list = request.form.get('input_country_list').split(";")
        for country in input_country_list:
            if country not in generic_country_list:
                input_country_list.remove(country)

        country_amount = len(input_country_list)

        if country_amount == 0:
            invalid = True
        else:
            input_country_list = sorted(input_country_list)

        # Gets a unique and persistent color for each country
        for country in input_country_list:
            color_list.append(get_color(country))

        year_min = int(request.form.get('selected_year_min'))
        year_max = int(request.form.get('selected_year_max'))
        per_capita_selector = request.form.get('selected_data')

        if per_capita_selector == "on":
            data_type = "emissions_per_capita"
        else:
            data_type = "emissions"

        if not invalid:
            data_dict = api_caller.get_multiple_data_range(input_country_list, data_type, year_min, year_max)

            # List of years for x axis labels, same for every country
            labels = list(data_dict[list(data_dict.keys())[0]].keys())

            # Assume no data was retrieved
            is_empty = True

            for i in range(len(input_country_list)):
                value_list = list(data_dict[list(data_dict.keys())[i]].values())
                values.append(value_list)

                # Check to see if any data present for this country
                for item in value_list:
                    if item is not None:
                        is_empty = False

    return render_template('index.html', generic_country_list=generic_country_list, generic_year_list=generic_year_list,
                           year_min=year_min, year_max=year_max, data_type=data_type, labels=labels, values=values,
                           received=received, is_empty=is_empty, invalid=invalid, input_country_list=input_country_list,
                           country_amount=country_amount, color_list=color_list, current_year=current_year)


# Api routing section

@app.route('/api/', methods=["GET"])
def api():
    return "<h1>Emission Visualizer API</h1>" \
           "<p>The API returns the following data in json format:</p>" \
           "<ul>" \
           "<li>api/country_list returns a list of available countries</li>" \
           "<li>api/country_id_list returns a list of countries with their corresponding ISO3 codes</li>" \
           "<li>api/data returns data for a specific country using the following arguments" \
           "<ul>" \
                "<li>Specify countries with countries= a comma separated list of ISO3 codes (required)</li>" \
                "<li>Specify type of data with data_type= emissions, emissions_per_capita or population " \
                "(defaults to emissions)</li>" \
                "<li>Specify specific year with year=int (defaults to a year range instead)</li>" \
                "<li>Specify a year range with year_min=int and year_max=int (defaults to all available data)</li>" \
           "</ul></li></ul>"


@app.route('/api/country_id_list', methods=["GET"])
def country_id_list():
    return jsonify(api_caller.get_country_id_dict())


@app.route('/api/country_list', methods=["GET"])
def country_list():
    return jsonify(api_caller.get_country_list())


@app.route('/api/data', methods=["GET"])
def data():
    request_data_type = request.args.get('data_type')
    request_year = request.args.get('year')
    request_country_string = request.args.get('countries')
    request_year_min = request.args.get('year_min')
    request_year_max = request.args.get('year_max')

    if request_year is not None:
        request_year = int(request_year)

    if request_year_min is None:
        request_year_min = 1960
    else:
        request_year_min = int(request_year_min)

    if request_year_max is None:
        request_year_max = api_caller.get_current_year()
    else:
        request_year_max = int(request_year_max)

    if request_data_type is None:
        request_data_type = 'emissions'

    if request_country_string is None:
        return "<h1>Please specify one or more valid countries</h1>" \
               "<p>Use countries=ISO,ISO,ISO... in the arguments.</p>"
    else:
        request_country_id_list = request_country_string.split(",")
        request_country_list = []
        for country in request_country_id_list:
            request_country_list.append(api_caller.get_country_name(country))

    if request_year is not None:
        request_year_max = request_year
        request_year_min = request_year

    return jsonify(api_caller.get_multiple_data_range(request_country_list, request_data_type, request_year_min,
                                                      request_year_max))


if __name__ == '__main__':
    app.run()
