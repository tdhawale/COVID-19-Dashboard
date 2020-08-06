# Julia Bresien
# Christopher Schrewing
# Soundarya Krishnan
# Tejas Ravindra Dhawale
# Rigers Sulku

import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import plotly.graph_objs as go # needed for the no data label

# URLs for downloading the CSV
url_population = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
url_deceased = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
url_confirmed_cases = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
url_recovered = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'


# Manual exceptions for countries that have a different name in the datasets. Datasets Cabo Verde, Diamond Princess, MS Zaandam, West Bank and Gaza will be ignored
# "JohnHopkinsName": "WorldInDataName"
hopkins_to_owid = {
    "Burma": "Myanmar",
    "Congo (Brazzaville)": "Congo",
    "Congo (Kinshasa)": "Democratic Republic of Congo",
    "Czechia": "Czech Republic",
    "Eswatini": "Swaziland",
    "Holy See": "Vatican",
    "Korea, South": "South Korea",
    "North Macedonia": "Macedonia",
    "Taiwan*": "Taiwan",
    "Timor-Leste": "Timor",
    "US": "United States"
}


def main():
    print("\nStarting Assignment 5\n")
    print("Fetching data:")
    # Get the basic dataframes from OWID and John Hopkins
    population_data = get_population_dataframe()
    deceased_data = get_john_hopkins_data(url_deceased)
    recovered_data = get_john_hopkins_data(url_recovered)
    cases_data = get_john_hopkins_data(url_confirmed_cases)

    print("\n\nAll data fetched, merging datasets:\n")
    # Create our own dataframe by aggregating different sources
    our_df = create_plot_dataframe(population_data, deceased_data, recovered_data, cases_data)

    print("\nData processing finished")
    print("\nPlotting.\n")

    # Whether to show this column on the hovering or not
    hover_data_display = {
        "population": True,
        "active": True,
        "confirmed": True,
        "recovered": True,
        "deceased": True,
        "isocode": False,
        "country": False,
        "date": False,
        "percOfPop": True
    }

    # Name to display on Screen
    data_labels = {
        "percOfPop": "Currently affected population percentage",
        "population": "Total Population",
        "active": "Active cases",
        "confirmed": "Total confirmed",
        "recovered": "Total recovered",
        "deceased": "Total deceased"
        # "isocode": "ISO-Code",
        # "country": "Country",
        # "date": "Date",
    }


    # Generates a choropleth map. Our main visualization
    fig = px.choropleth(our_df, 
                        title = "Active COVID-19 cases (in relation to total population of country)",
                        locations="isocode",
                        color="percOfPop",  # This will determine the color
                        hover_name="country",  # column to add to hover information
                        animation_frame="date", # add a slider which changes the map's data according to the date selected (between 22.1.20 till current date)
                        hover_data = hover_data_display,
                        labels = data_labels,
                        # range_color = range_of_color,
                        color_continuous_scale=px.colors.sequential.YlOrRd)  # Find colorscales here https://plotly.com/python/builtin-colorscales/#builtin-sequential-color-scales

    number_of_days = len(cases_data.columns.tolist()[1:]) # checking how many columns are in the dataset -> total number of days available 

    fig.update_layout(
        coloraxis_colorbar=dict(ticks="outside", ticksuffix=" %"), # configuring the colorbar
        sliders=[dict(active=number_of_days)], # the slider should start at right side (newest date), not on the left, so setting it to the right with 'active' attribute   
        
        # adding a "No data" label manually
        annotations = [
            go.layout.Annotation( # first add the bright grey color as one element
            text = '      ' ,
            align = 'left' ,
            showarrow = False ,
            xref = 'paper' ,
            yref = 'paper' ,
            x = 1.08,
            y = -0.1 ,
            bordercolor = 'black' ,
            borderwidth = 1,
            bgcolor = "#E5ECF6"
            ) ,
            
            go.layout.Annotation( # then add the label "no data" as one element
            text = 'No data' ,
            align = 'left' ,
            showarrow = False ,
            xref = 'paper' ,
            yref = 'paper' ,
            x = 1.14,
            y = -0.1 ,
            )]
    )

    fig.show()
    print("\nEverything is done. Have a nice day!\n")


# This creates the following dataset, prepared with regards to this tutorial https://amaral.northwestern.edu/blog/step-step-how-plot-map-slider-represent-time-evolu
# isocode   country     date    confirmed   recovered   deceased    active      population      percOfPop
#   GER     Germany   6/16/20   160000      150000      5000        5000        80000000        0,0000625
#   GER     Germany   6/17/20   160400      150000      5000        5400        80000000        0,0000675
# ....
#   FRA     France    6/16/20   160000      100000      5000        5000        60000000        0,0000734
# ....
def create_plot_dataframe(population_data, deceased_data, recovered_data, cases_data):
    for hop_name in hopkins_to_owid:    # Go through all manual naming exceptions and apply them to the John-Hopkins Data (I think the ourworld in data names are nicer)
        owi_name = hopkins_to_owid[hop_name]
        deceased_data = deceased_data.replace(hop_name, owi_name)
        recovered_data = recovered_data.replace(hop_name, owi_name)
        cases_data = cases_data.replace(hop_name, owi_name)

    list_of_countries = cases_data['Country/Region'].tolist()   # Get all country names as a list
    list_of_dates = cases_data.columns.tolist()[1:]             # Get all the dates we have data for by using the column names of JohnHopkinsData as a list and discarding the first element.
    
    # Create a list of countries we will ignore. Seriously: deleting rows in a dataframe is ridiculously annoying.
    countries_to_drop = []
    for country in list_of_countries:
        if not country in population_data.location.values: # If it is not in the OWID dataset, delete it from the hopkins datasets
            print("No Population data for: ", country, "\ncountry will be ignored.\n")
            countries_to_drop.append(country)
            


    our_columns = ['isocode', 'country', 'date', 'confirmed', 'recovered', 'deceased', 'active', 'population', 'percOfPop']
    our_rows = [] # This will be a list containing lists. Every list in our_rows will be a row in the dataframe. So a countries status at one date

    print("\nStarting number crunching, this might take a while...")
    # Now we go one by one through the countries and through the dates, each time creating a row in our new dataframe.
    for country in list_of_countries:
        if country in countries_to_drop: continue # If we do not have enough data available we skip this country.
        isocode = get_val_by_country(population_data, 'iso_code', country)
        country = country
        population = get_val_by_country(population_data, 'population', country)

        deceased_row = get_country_row(deceased_data, country)      # Get the row of the current country, with the columns as the dates and the values in one single row. Do this for the every hopkins dataset we have
        recovered_row = get_country_row(recovered_data, country)    # Country/Region    1/22/20 1/23/20 ...
        cases_row = get_country_row(cases_data, country)            #     Germany         0        0          
        for date in list_of_dates:
            deceased =  get_val_at_date(deceased_row, date)     # Get the value for the specified at country at the specified date
            recovered = get_val_at_date(recovered_row, date)
            confirmed = get_val_at_date(cases_row, date)
            active = confirmed - recovered - deceased
            percOfPop = float( active / population ) * 100 # will be value in percent: percofpop = 5 means 5 percent

            new_row = [isocode, country, date, confirmed, recovered, deceased, active, population, percOfPop] # This line holds all the information for a single country at one particular date
            our_rows.append(new_row)

            # Workaround: to actually show the newest date per default: copy the last column to the first position
            # Needed because only setting the slider to right side will sadly not update the frame view... (known and still unsolved bug)
            if list_of_dates.index(date) == len(list_of_dates)-1: # checking for last element, because this should be the first element as well
                our_rows.insert(0, [isocode, country, "MM/DD/YY", confirmed, recovered, deceased, active, population, percOfPop]) # instead of showing the day (which would be very strange...), misuse the label as a legend
            
    print("...done crunching.")
    # Now we have a list containing lists. Every contained list will be a row in our new dataframe.
    # Create the dataframe now:
    ourdataframe = pd.DataFrame(our_rows, columns = our_columns)
    return ourdataframe


def get_val_by_country(population_data, wanted_val, country):
    position = population_data['location'] == country # get a list containing TRUE at the positions where Germany is (hopefully only one in our case)
    result = population_data[position][wanted_val].tolist()[0] # get the subdataframe containing only rows, where position is TRUE. Then get only the wanted_val column. Turn it into a list. Get the first element from the list.
    return result


def get_country_row(hopkins_data, country):
    position_country = hopkins_data['Country/Region'] == country # get a list containing TRUE at the positions where Germany is (hopefully only one in our case)
    result = hopkins_data[position_country] # get the subdataframe containing only rows, where position is TRUE. Then get only the wanted_val column. Turn it into a list. Get the first element from the list.
    return result


# Only meant to be used when you have a single row for a country
def get_val_at_date(hopkins_country_data_row, date):
    return hopkins_country_data_row[date].tolist()[0] # Get the column with the name 'date', turn it into a list and get the first (and only) element


# Creates a dataframe as follows
# isocode location population
# ALB     Albania  2877800.0
# AND     Andorra    77265.0
def get_population_dataframe():
    with urlopen(url_population) as response:
        ourworldindata = pd.read_csv(response)

    # ['iso_code', 'continent', 'location', 'date', 'total_cases', 'new_cases', 'total_deaths', 'new_deaths', 'total_cases_per_million', 'new_cases_per_million', 'total_deaths_per_million', 'new_deaths_per_million', 'total_tests', 'new_tests', 'total_tests_per_thousand', 'new_tests_per_thousand', 'new_tests_smoothed', 'new_tests_smoothed_per_thousand', 'tests_units', 'stringency_index', 'population', 'population_density', 'median_age', 'aged_65_older', 'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 'cvd_death_rate', 'diabetes_prevalence', 'female_smokers', 'male_smokers', 'handwashing_facilities', 'hospital_beds_per_thousand', 'life_expectancy']
    needed_cols = ['iso_code', 'location', 'population'] # Only these columns will be kept
    ourworldindata = ourworldindata.filter(needed_cols) # Remove all but needed_cols from the dataframe
    ourworldindata = ourworldindata.drop_duplicates(subset='iso_code') # We only need one entry for each country for our plot. So we only keep one row per country.
    ourworldindata.drop(ourworldindata.tail(2).index,inplace=True) # drop last 2 rows (contained international and total world population)
    print("Data received: ", url_population)
    return ourworldindata




# Creates a dataframe in the following format
# Country/Region    1/22/20 1/23/20 ..  6/16/20
# Germany           0       0           500
# Georgia           0       0           350
def get_john_hopkins_data(url):
    with urlopen(url) as response:
        johns_hopkins_generic = pd.read_csv(response)

    unwanted_cols = ['Province/State', 'Lat', 'Long'] # Every column besides these will be kept
    johns_hopkins_generic = johns_hopkins_generic.drop(unwanted_cols, axis=1) # Remove the unwanted Columns axis=1 means we drop columns not rows
    johns_hopkins_generic = johns_hopkins_generic.groupby('Country/Region',as_index=False).agg("sum") # Group by country name and aggregate all columns by summing them up.

    print("Data received: ", url)
    return johns_hopkins_generic

main()
