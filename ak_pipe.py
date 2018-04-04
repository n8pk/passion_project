import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from geopy.distance import vincenty

for n in range(1994, 2015):
    # reading in files, and making the big dataframe

    year = n
    weather_year = pd.read_csv('/home/nate/Desktop/fires/west/{}.csv'.format(year), header=None)

    stations = pd.read_pickle('murica_stations.pkl')

    ak_fires = pd.read_pickle('pnw_df.pkl')


    # cut down weather data

    weather_year = weather_year[[0,1,2,3]]
    weather_year.columns = ['station', 'date', 'data_type', 'measurement']

    weather_year = weather_year.set_index('station').join(stations.set_index('code'))
    weather_year = weather_year.dropna()

    weather_year = weather_year[weather_year['lon'] < -116]
    weather_year = weather_year[weather_year['lon'] > -125]
    weather_year = weather_year[weather_year['lat'] < 50]
    weather_year = weather_year[weather_year['lat'] > 41]


    # index col

    weather_year['station'] = weather_year.index


    # feature making!!!

    tmax = []
    tmin = []
    prcp = []
    snow = []

    for idx, row in weather_year.iterrows():
        if row[1] == 'TMAX':
            tmax.append(float(row[2]/10))
            tmin.append(0)
            prcp.append(0)
            snow.append(0)
        elif row[1] == 'TMIN':
            tmax.append(0)
            tmin.append(float(row[2]/10))
            prcp.append(0)
            snow.append(0)
        elif row[1] == 'PRCP':
            tmax.append(0)
            tmin.append(0)
            prcp.append(row[2])
            snow.append(0)
        elif row[1] == 'SNOW':
            tmax.append(0)
            tmin.append(0)
            prcp.append(0)
            snow.append(row[2])
        else:
            tmax.append(0)
            tmin.append(0)
            prcp.append(0)
            snow.append(0)

    weather_year['tmax'] = tmax
    weather_year['tmin'] = tmin
    weather_year['prcp'] = prcp
    weather_year['snow'] = snow


    # cleanup all the stuff
    # we have some unnecessary cols, and we can push 4 rows into one to get all the
    # features we want in one place
    # after grouping it's time to get coordinates on the stations, and
    # if we don't know where a station is we need to drop it
    # date also has to be fixed

    weather_year = weather_year.drop(['data_type', 'measurement'], axis=1)
    weather_year = weather_year.groupby(['date', 'station'])['tmax', 'tmin', 'prcp', 'snow'].sum().reset_index()

    weather_year = weather_year.set_index('station').join(stations.set_index('code'))
    weather_year = weather_year.dropna()

    weather_year['clean_date'] = pd.to_datetime(weather_year['date'], format='%Y%m%d')

    weather_year = weather_year.reset_index()
    ak_fires = ak_fires.reset_index()
    ak_fires_year = ak_fires[ak_fires['YEAR'] == year]
    ak_fires_year = ak_fires_year.reset_index()


    # beautiful Vincenty function
    # there's quite a bit of complexity here, because we're literally finding the
    # distance between each fire's ignition point and every weather station in the
    # region in order to find the closest one. sometimes they're 0.1 miles, sometimes
    # they're 100 miles... in Alaska... where noone lives... just bears, and bears do
    # not build weather stations

    avg_tmax = []
    avg_tmin = []
    avg_prcp = []
    avg_snow = []
    prcp_7 = []
    prcp_14 = []
    prcp_28 = []

    for idx, fire in ak_fires_year.iterrows():

        date = ak_fires_year.iloc[idx][8]
        dist = []
        stations_day = weather_year[weather_year['clean_date'] == date]
        stations_day.reset_index()

        for idy, station in stations_day.iterrows():
            dist.append((idy, vincenty((fire[3], fire[4]), (station[6], station[7])).miles))

        dist.sort(key=lambda x: x[1])
        distx = [tup[0] for tup in dist[:1]]

        avg_tmax.append(np.mean([weather_year.iloc[i][2] for i in distx]))
        avg_tmin.append(np.mean([weather_year.iloc[i][3] for i in distx]))
        avg_prcp.append(np.mean([weather_year.iloc[i][4] for i in distx]))
        avg_snow.append(np.mean([weather_year.iloc[i][5] for i in distx]))

        p_7 = 0
        for d in distx:
            for i in range(7):
                p_7 += weather_year.iloc[d-i][4]
        prcp_7.append(p_7)

        p_14 = 0
        for d in distx:
            for i in range(14):
                p_14 += weather_year.iloc[d-i][4]
        prcp_14.append(p_14)

        p_28 = 0
        for d in distx:
            for i in range(28):
                p_28 += weather_year.iloc[d-i][4]
        prcp_28.append(p_28)

    ak_fires_year['tmax_5'] = avg_tmax
    ak_fires_year['tmin_5'] = avg_tmin
    ak_fires_year['prcp_5'] = avg_prcp
    ak_fires_year['snow_5'] = avg_snow
    ak_fires_year['last_7'] = prcp_7
    ak_fires_year['last_14'] = prcp_14
    ak_fires_year['last_28'] = prcp_28

    ak_fires_year = ak_fires_year.drop(['level_0', 'index'], axis=1)

    ak_fires_year.to_csv('/home/nate/Desktop/fires/west/{}_fires.csv'.format(year))