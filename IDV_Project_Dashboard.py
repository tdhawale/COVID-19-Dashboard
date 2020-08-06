# Julia Bresien
# Christopher Schrewing
# Soundarya Krishnan
# Tejas Ravindra Dhawale
# Rigers Sulku

import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import dash
import dash_core_components as dcc
import dash_html_components as html
import time
from plotly.subplots import make_subplots
import numpy as np
import plotly.graph_objects as go
from datetime import datetime as dt
from dash.dependencies import Input , Output , State

# --------------------------------------------------------------------------------------
# Start the dash app
app = dash.Dash(__name__)
# --------------------------------------------------------------------------------------
# Pr-processing the data

# URLs for downloading the CSV
url_population = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
url_deceased = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
url_confirmed_cases = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
url_recovered = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
url_country = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_country.csv'

# Manual exceptions for countries that have a different name in the datasets. Datasets Cabo Verde, Diamond Princess, MS Zaandam, West Bank and Gaza will be ignored
# "JohnHopkinsName": "WorldInDataName"
hopkins_to_owid = {
	"Burma" : "Myanmar" ,
	"Congo (Brazzaville)" : "Congo" ,
	"Congo (Kinshasa)" : "Democratic Republic of Congo" ,
	"Czechia" : "Czech Republic" ,
	"Eswatini" : "Swaziland" ,
	"Holy See" : "Vatican" ,
	"Korea, South" : "South Korea" ,
	"North Macedonia" : "Macedonia" ,
	"Taiwan*" : "Taiwan" ,
	"Timor-Leste" : "Timor" ,
	"US" : "United States"
}


# This creates the following dataset, prepared with regards to this tutorial https://amaral.northwestern.edu/blog/step-step-how-plot-map-slider-represent-time-evolu
# isocode   country     date    confirmed   recovered   deceased    active      population      ActPerPop
#   GER     Germany   6/16/20   160000      150000      5000        5000        80000000        0,0000625
#   GER     Germany   6/17/20   160400      150000      5000        5400        80000000        0,0000675
# ....
#   FRA     France    6/16/20   160000      100000      5000        5000        60000000        0,0000734
# ....
def create_plot_dataframe(population_data , deceased_data , recovered_data , cases_data) :
	for hop_name in hopkins_to_owid :  # Go through all manual naming exceptions and apply them to the John-Hopkins Data (I think the ourworld in data names are nicer)
		owi_name = hopkins_to_owid[hop_name]
		deceased_data = deceased_data.replace(hop_name , owi_name)
		recovered_data = recovered_data.replace(hop_name , owi_name)
		cases_data = cases_data.replace(hop_name , owi_name)
	
	list_of_countries = cases_data['Country/Region'].tolist()  # Get all country names as a list
	list_of_dates = cases_data.columns.tolist()[
	                1 :]  # Get all the dates we have data for by using the column names of JohnHopkinsData as a list and discarding the first element.
	
	# Create a list of countries we will ignore. Seriously: deleting rows in a dataframe is ridiculously annoying.
	countries_to_drop = []
	print("No Population data for the following countries. Thus the countries will be ignored.\n")
	# print("[ ")
	for country in list_of_countries :
		if not country in population_data.location.values :  # If it is not in the OWID dataset, delete it from the hopkins datasets
			# print("No Population data for: " , country , "\ncountry will be ignored.\n")
			# print(country , " ")
			countries_to_drop.append(country)
	print(countries_to_drop)
		
	our_columns = ['isocode' , 'country' , 'date' , 'confirmed' , 'recovered' , 'deceased' , 'active' , 'population' ,
	               'ActPerPop' , 'CnfPerPop' , 'RecPerCnf' , 'DecPerCnf']
	our_rows = []  # This will be a list containing lists. Every list in our_rows will be a row in the dataframe. So a countries status at one date
	
	print("\nStarting number crunching, this might take a while...")
	# Now we go one by one through the countries and through the dates, each time creating a row in our new dataframe.
	for country in list_of_countries :
		if country in countries_to_drop : continue  # If we do not have enough data available we skip this country.
		isocode = get_val_by_country(population_data , 'iso_code' , country)
		country = country
		population = get_val_by_country(population_data , 'population' , country)
		
		deceased_row = get_country_row(deceased_data ,
		                               country)  # Get the row of the current country, with the columns as the dates and the values in one single row. Do this for the every hopkins dataset we have
		recovered_row = get_country_row(recovered_data , country)  # Country/Region    1/22/20 1/23/20 ...
		cases_row = get_country_row(cases_data , country)  # Germany         0        0
		for date in list_of_dates :
			deceased = get_val_at_date(deceased_row ,
			                           date)  # Get the value for the specified at country at the specified date
			recovered = get_val_at_date(recovered_row , date)
			confirmed = get_val_at_date(cases_row , date)
			active = confirmed - recovered - deceased
			ActPerPop = float(active / population)
			CnfPerPop = float(confirmed / population)
			if confirmed != 0 :
				RecPerCnf = float(recovered / confirmed)
				DecPerCnf = float(deceased / confirmed)
			else :
				RecPerCnf = 0
				DecPerCnf = 0
			
			new_row = [isocode , country , date , confirmed , recovered , deceased , active , population ,
			           ActPerPop , CnfPerPop , RecPerCnf ,
			           DecPerCnf]  # This line holds all the information for a single country at one particular date
			our_rows.append(new_row)
	print("...done crunching.")
	# Now we have a list containing lists. Every contained list will be a row in our new dataframe.
	# Create the dataframe now:
	ourdataframe = pd.DataFrame(our_rows , columns = our_columns)
	
	#dates = ourdataframe["date"].tolist()
	#print(dates)
	
	return ourdataframe


def get_val_by_country(population_data , wanted_val , country) :
	position = population_data[
		           'location'] == country  # get a list containing TRUE at the positions where Germany is (hopefully only one in our case)
	result = population_data[position][wanted_val].tolist()[
		0]  # get the subdataframe containing only rows, where position is TRUE. Then get only the wanted_val column. Turn it into a list. Get the first element from the list.
	return result


def get_country_row(hopkins_data , country) :
	position_country = hopkins_data[
		                   'Country/Region'] == country  # get a list containing TRUE at the positions where Germany is (hopefully only one in our case)
	result = hopkins_data[
		position_country]  # get the subdataframe containing only rows, where position is TRUE. Then get only the wanted_val column. Turn it into a list. Get the first element from the list.
	return result


# Only meant to be used when you have a single row for a country
def get_val_at_date(hopkins_country_data_row , date) :
	return hopkins_country_data_row[date].tolist()[
		0]  # Get the column with the name 'date', turn it into a list and get the first (and only) element


# Creates a dataframe as follows
# isocode location population
# ALB     Albania  2877800.0
# AND     Andorra    77265.0
def get_population_dataframe() :
	with urlopen(url_population) as response :
		ourworldindata = pd.read_csv(response)
	
	# ['iso_code', 'continent', 'location', 'date', 'total_cases', 'new_cases', 'total_deaths', 'new_deaths', 'total_cases_per_million', 'new_cases_per_million', 'total_deaths_per_million', 'new_deaths_per_million', 'total_tests', 'new_tests', 'total_tests_per_thousand', 'new_tests_per_thousand', 'new_tests_smoothed', 'new_tests_smoothed_per_thousand', 'tests_units', 'stringency_index', 'population', 'population_density', 'median_age', 'aged_65_older', 'aged_70_older', 'gdp_per_capita', 'extreme_poverty', 'cvd_death_rate', 'diabetes_prevalence', 'female_smokers', 'male_smokers', 'handwashing_facilities', 'hospital_beds_per_thousand', 'life_expectancy']
	needed_cols = ['iso_code' , 'location' , 'population']  # Only these columns will be kept
	ourworldindata = ourworldindata.filter(needed_cols)  # Remove all but needed_cols from the dataframe
	ourworldindata = ourworldindata.drop_duplicates(
		subset = 'iso_code')  # We only need one entry for each country for our plot. So we only keep one row per country.
	ourworldindata.drop(ourworldindata.tail(2).index ,
	                    inplace = True)  # drop last 2 rows (contained international and total world population)
	print("Data received: " , url_population)
	return ourworldindata


# Creates a dataframe in the following format
# Country/Region    1/22/20 1/23/20 ..  6/16/20
# Germany           0       0           500
# Georgia           0       0           350
def get_john_hopkins_data(url) :
	with urlopen(url) as response :
		johns_hopkins_generic = pd.read_csv(response)
	
	if ('cases_country' in url) == True:
		unwanted_cols = ['Last_Update','Lat' ,'Long_']  # Every column besides these will be kept
		johns_hopkins_generic = johns_hopkins_generic.drop(unwanted_cols ,
		                                                   axis = 1)
		# johns_hopkins_generic.rename(columns = {'Country_Region' : 'country'})
		print("Data received: " , url)
		return johns_hopkins_generic
	else:
		unwanted_cols = ['Province/State' , 'Lat' , 'Long']  # Every column besides these will be kept
		johns_hopkins_generic = johns_hopkins_generic.drop(unwanted_cols ,
	                                                       axis = 1)  # Remove the unwanted Columns axis=1 means we drop columns not rows
		johns_hopkins_generic = johns_hopkins_generic.groupby('Country/Region' , as_index = False).agg(
			"sum")  # Group by country name and aggregate all columns by summing them up.
		print("Data received: " , url)
		return johns_hopkins_generic
	
	

print("--------------------------------------------------------------------------------------------------------------")
print()
population_data = get_population_dataframe()
deceased_data = get_john_hopkins_data(url_deceased)
recovered_data = get_john_hopkins_data(url_recovered)
cases_data = get_john_hopkins_data(url_confirmed_cases)

# For total count plot and to determine worst hit countries
country_data = get_john_hopkins_data(url_country)
print(country_data.head())
print()
print("--------------------------------------------------------------------------------------------------------------")
# For Geographical plot date wise
our_df = create_plot_dataframe(population_data , deceased_data , recovered_data , cases_data)
date_slider = our_df['date'].unique().tolist()
YEARS = {i : date_slider[i] for i in range(0 , len(date_slider))}
print(YEARS.keys())
print(YEARS.values())

# The read data from john hopkins
#   Country/Region  1/22/20  1/23/20  1/24/20  ...  6/16/20  6/17/20  6/18/20  6/19/20
# 0    Afghanistan        0        0        0  ...      491      504      546      548
# 1        Albania        0        0        0  ...       37       38       39       42
# 2        Algeria        0        0        0  ...      788      799      811      825
# 3        Andorra        0        0        0  ...       52       52       52       52
# 4         Angola        0        0        0  ...        6        7        8        8

# What goes into the app layout is
# The Dash components
# The grphs, drop downs , checkbox
# ---------------------------------------------------------------------------------------------
DEFAULT_OPACITY = 0.8

mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"


# App Layout
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
	            # Logo commented
                html.Img(id="logo", src="upb-logo.png"),
                html.H4(children="COVID 19 Analysis dashboard"),
                html.P(
                    id="description",
                    children="This Dashboard gives you an detailed insight of the \
                    COVID 19 pandemic across the world.",
                ),
            ],
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                ),
                                dcc.Slider(
                                    id="years-slider",
                                    min= min(YEARS.keys()),
                                    max=max(YEARS.keys()),
                                    value=min(YEARS.keys()),
                                    # marks={
	                                #     i: '{}'.format(i) for i in YEARS.keys()
	                                #     # str(year): '{}'.format(year) for year in  YEARS.items()
                                    #     # str(year): {
                                    #     #     "label": str(year),
                                    #     #     "style": {"color": "#7fafdf"},
                                    #     # }
                                    #     # for year in YEARS.values()
                                    # },
                                ),
                            ],
                        ),
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.P(
                                    "World Map Statistics",
                                    id="heatmap-title",
                                ),
	                            dcc.Dropdown(id = "select_cat" ,
	                                         options = [
		                                         {'label' : 'Active Cases' , 'value' : 'ActPerPop'} ,
		                                         {'label' : 'Confirmed Cases' , 'value' : 'CnfPerPop'} ,
		                                         {'label' : 'Recovered Cases' , 'value' : 'RecPerCnf'} ,
		                                         {'label' : 'Deaths' , 'value' : 'DecPerCnf'}
	                                         ] ,
	                                         multi = False ,
	                                         value = 'ActPerPop' ,
	                                         style = {'width' : "40%"}
	                                         ) ,
                                dcc.Graph(
                                    id="world-choropleth",
	                                # figure = {}
                                    figure=dict(
                                        layout=dict(
                                            mapbox=dict(
                                                layers=[],
                                                accesstoken=mapbox_access_token,
                                                style=mapbox_style,
                                                center=dict(
                                                    lat=38.72490, lon=-95.61446
                                                ),
                                                pitch=0,
                                                zoom=3.5,
                                            ),
                                            autosize=True,
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="graph-container",
                    children=[
                        html.P(id="chart-selector", children="Select Country:"),
						dcc.Dropdown(id = "select_country" ,
	                        options = [{'label' : 'Afganistan' , 'value' : 'Afganistan'} ,
		                               {'label' : 'Albania' , 'value' : 'Albania'} ,
		                               {'label' : 'Algeria' , 'value' : 'Algeria'}] ,
	                        multi = False ,
	                        value = 'Algeria' ,
	                        style = {'width' : "40%"}) ,
	                    
	                    
                        dcc.Graph(
                            id="line-chart",
                            figure=dict(
                                data=[dict(x=0, y=0)],
                                layout=dict(
                                    paper_bgcolor="#F4F4F8",
                                    plot_bgcolor="#F4F4F8",
                                    autofill=True,
                                    margin=dict(t=75, r=50, b=100, l=50),
                                ),
                            ),
                        ),
                    ],
                ),
	            html.Div([
		
		            # HTML Header
		            html.H1("Please write some header" , style = {'text-align' : 'center'}) ,
		
		            dcc.Slider(
			            id = 'slider',
			            min = 1 ,
			            max = 30 ,
			            step = 1 ,
			            value = 10
		            ) ,
					dcc.RadioItems(
						id = 'radio_button',
					    options=[
					        {'label': 'Active Cases', 'value': 'Active'},
					        {'label': 'Confirmed Cases', 'value': 'Confirmed'},
					        {'label': 'Death Cases', 'value': 'Death'},
					        {'label': 'Recovered', 'value': 'Recovered'}
					    ],
					    value='Active',
					    labelStyle={'display': 'inline-block'}
					),
		            html.Br() ,
	
		            dcc.Graph(id = 'bubble_chart' , figure = {})
	
	            ]),
	            html.Div([
		
		            # HTML Header
		            html.H1("Total Count" , style = {'text-align' : 'center'}) ,
		            html.Br() ,
		
		            dcc.Graph(id = 'total_count' , figure = {})
	
	            ])
            ],
        ),
    ],
)


@app.callback(
	Output('world-choropleth' , 'figure'),
	[Input('select_cat' , 'value') ,
	 Input("years-slider", "value")],
)
def update_graph(cat_selected , date_selected ) :
	print(cat_selected)
	print(date_selected)
	date = YEARS.get(date_selected)
	only_one_day = our_df[our_df['date'] == date]
	if cat_selected == 'ActPerPop' :
		fig = px.choropleth(only_one_day , locations = "isocode" ,
		                    color = "ActPerPop" ,  # This will determine the color
		                    hover_name = "country" ,  # column to add to hover information
		                    # template = 'plotly_dark' ,
		                    width = 1300,
		                    height = 500,
		                    color_continuous_scale = px.colors.sequential.YlOrRd)
	if cat_selected == 'CnfPerPop' :
		fig = px.choropleth(only_one_day , locations = "isocode" ,
		                    color = "CnfPerPop" ,  # This will determine the color
		                    hover_name = "country" ,  # column to add to hover information
		                    # template = 'plotly_dark' ,
		                    width = 1300 ,
		                    height = 500 ,
		                    color_continuous_scale = px.colors.sequential.YlOrRd)
	
	if cat_selected == 'RecPerCnf' :
		fig = px.choropleth(only_one_day , locations = "isocode" ,
		                    color = "RecPerCnf" ,  # This will determine the color
		                    hover_name = "country" ,  # column to add to hover information
		                    # template = 'plotly_dark'
		                    width = 1300 ,
		                    height = 500 ,
		                    color_continuous_scale = px.colors.sequential.YlOrRd)
	
	if cat_selected == 'DecPerCnf' :
		fig = px.choropleth(only_one_day , locations = "isocode" ,
		                    color = "DecPerCnf" ,  # This will determine the color
		                    hover_name = "country" ,  # column to add to hover information
		                    # template = 'plotly_dark' ,
		                    width = 1300 ,
		                    height = 500 ,
		                    color_continuous_scale = px.colors.sequential.YlOrRd)
		
	fig.update_layout(
		# title = str(date_selected) + " Worst hit countries" ,
		title = "Date Selected is : " + date ,
		# width = 1200,
		autosize = True,
		# margin = dict(l = 40 , r = 40 , t = 40 , b = 40) ,
	    paper_bgcolor = "LightSteelBlue" ,
	)
	#
	# if "layout" in figure :
	# 	lat = figure["layout"]["mapbox"]["center"]["lat"]
	# 	lon = figure["layout"]["mapbox"]["center"]["lon"]
	# 	zoom = figure["layout"]["mapbox"]["zoom"]
	# else :
	lat = 38.72490
	lon = -95.61446
	zoom = 3.5
	
	layout = dict(
		mapbox = dict(
			layers = [] ,
			accesstoken = mapbox_access_token ,
			style = mapbox_style ,
			center = dict(lat = lat , lon = lon) ,
			zoom = zoom ,
		) ,
		hovermode = "closest" ,
		margin = dict(r = 0 , l = 0 , t = 0 , b = 0) ,
		# annotations = annotations ,
		dragmode = "lasso" ,
	)
	
	# fig = dict( layout = layout)
	
	return fig

@app.callback(Output("line-chart", "figure"), [Input('select_country' , 'value')])
def display_line_chart(country):
	df_list = [cases_data, recovered_data, deceased_data]
	labels = ['confirmed' ,'recovered', 'deaths']
	colors = ['blue' , 'yellow' , 'red']
	# mode_size = [6 , 8, 10]
	# line_size = [4 , 5 , 6]
	fig = go.Figure();
	
	for i , df in enumerate(df_list) :
		x_data = np.array(list(df.iloc[: , 1 :].columns))
		y_data = np.sum(np.asarray(df[df['Country/Region'] == country].iloc[: , 1 :]) , axis = 0)
		
		fig.add_trace(go.Scatter(x = x_data , y = y_data , mode = 'lines+markers' ,
		                         name = labels[i] ,
		                         line = dict(color = colors[i] ) ,#, width = line_size[i]
		                         connectgaps = True ,
		                         text = "Total " + str(labels[i]) + ": " + str(y_data[-1])
		                         ));


		fig.update_layout(title = "COVID 19 cases of " + country ,
		                  xaxis_title = 'Date' ,
		                  yaxis_title = 'No. of Confirmed Cases' ,
		                  margin = dict(l = 40 , r = 20 , t = 40 , b = 20) ,
		                  paper_bgcolor = "lightgrey" ,
		                  width = 800 );

		fig.update_yaxes(type = "linear")
		
	return fig







@app.callback(Output("bubble_chart", "figure"), [ Input("years-slider", "value"), Input('slider' , 'value'),
                                                  Input('radio_button' , 'value')])
def update_bubble_chart(date_selected, n , radio_button):
	date = YEARS.get(date_selected)
	
	if radio_button == 'Active':
		sorted_country_df = our_df[our_df['date'] == date].sort_values('active' , ascending = False)
		sorted_country_df = sorted_country_df.head(n)
		fig = px.scatter(sorted_country_df.head(n) , x = "country" , y = "active" , size = "active" ,
		                 color = "country" ,
		                 hover_name = "country" , size_max = 60)
		
		fig.update_layout(
			title = str(n) + " Worst hit countries dated on (" + date + ")" ,
			xaxis_title = "Countries" ,
			yaxis_title = "Active Cases" ,
			width = 1300
		)
		
	elif radio_button =='Confirmed':
		sorted_country_df = our_df[our_df['date'] == date].sort_values('confirmed' , ascending = False)
		sorted_country_df = sorted_country_df.head(n)
		fig = px.scatter(sorted_country_df.head(n) , x = "country" , y = "confirmed" , size = "confirmed" ,
		                 color = "country" ,
		                 hover_name = "country" , size_max = 60)
		
		fig.update_layout(
			title = str(n) + " Worst hit countries dated on (" + date + ")" ,
			xaxis_title = "Countries" ,
			yaxis_title = "Confirmed Cases" ,
			width = 1300
		)
		
	elif radio_button == 'Death':
		sorted_country_df = our_df[our_df['date'] == date].sort_values('deceased' , ascending = False)
		sorted_country_df = sorted_country_df.head(n)
		fig = px.scatter(sorted_country_df.head(n) , x = "country" , y = "deceased" , size = "deceased" ,
		                 color = "country" ,
		                 hover_name = "country" , size_max = 60)
		
		fig.update_layout(
			title = str(n) + " Worst hit countries dated on (" + date + ")" ,
			xaxis_title = "Countries" ,
			yaxis_title = "Death Cases" ,
			width = 1300
		)
		
	elif radio_button == 'Recovered':
		sorted_country_df = our_df[our_df['date'] == date].sort_values('recovered' , ascending = False)
		sorted_country_df = sorted_country_df.head(n)
		fig = px.scatter(sorted_country_df.head(n) , x = "country" , y = "recovered" , size = "recovered" ,
		                 color = "country" ,
		                 hover_name = "country" , size_max = 60)
		
		fig.update_layout(
			title = str(n) + " Worst hit countries dated on (" + date + ")" ,
			xaxis_title = "Countries" ,
			yaxis_title = "Recovered Cases" ,
			width = 1300
		)
		
	


	
	# )
	return fig


@app.callback(Output("total_count", "figure"),  [Input("years-slider", "value")])
def update_total_count(date_selected):
	date = YEARS.get(date_selected)
	names = ['Active','Confirmed', 'Deaths', 'Recovered']
	values = [int(our_df[our_df['date']== date]['active'].sum()),
	          int(our_df[our_df['date']== date]['confirmed'].sum()),
	          int(our_df[our_df['date'] == date]['deceased'].sum()),
	          int(our_df[our_df['date'] == date]['recovered'].sum())]
	colors = ['lightslategray', 'yellow' , 'red', 'green']
	
	fig = go.Figure(data = [go.Bar(
		x = names ,
		y = values ,
		marker_color = colors  # marker color can be a single color value or an iterable
	)])
	fig.update_layout(title_text = 'Total Global Count')
	
	return fig



# ------------------------------------------------------------------------------
if __name__ == '__main__' :
	app.run_server(debug = True)

