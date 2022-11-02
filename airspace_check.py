import csv
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import time
import datetime

from matplotlib.path import Path
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


# Path to file containing flight tracking information
tracking_filepath = os.path.abspath('AD4361_2dcc7ee7.csv')

# Aerodrome ICAO code
# ad_icao = 'SBKP'

# Runway strip
rwy_thr_xs = [-47.14694, -47.12194]
rwy_thr_ys = [-22.99861, -23.01639]

# CTR Campinas' vertical limits
ctr_upper_limit = 3700
ctr_lower_limit = 0

# List of points delimiting CTR Campinas' horizontal limits
ctr_coords = [
    (-47.05833, -23.15639),
    (-46.95333, -23.03056),
    (-47.23694, -22.8275),
    (-47.36833, -22.98472),
    (-47.14778, -23.14306),
    (-47.05833, -23.15639)
]

# TMA São Paulo 2's vertical limits
tma2_upper_limit = 5500
tma2_lower_limit = 3600

# List of points delimiting TMA São Paulo 2's horizontal limits
tma2_coords = [
    (-47.17722222200, -22.7633333330),
    (-47.07132252390, -22.8399787568),
    (-46.96530416120, -22.9165529453),
    (-46.85916666700, -22.9930555560),
    (-46.74861111100, -22.9850000000),
    (-46.65172677510, -23.0689190695),
    (-46.55472222200, -23.1527777780),
    (-46.38339956780, -23.2048157536),
    (-46.21194444400, -23.2566666670),
    (-46.13666666700, -23.3822222220),
    (-46.23866024820, -23.5299774042),
    (-46.34088179830, -23.6776628004),
    (-46.44333333300, -23.8252777780),
    (-46.54887798310, -23.8387861596),
    (-46.65444444400, -23.8522222220),
    (-46.79390572640, -23.7572562394),
    (-46.93316467380, -23.6621633984),
    (-47.07222222200, -23.5669444440),
    (-47.08849215850, -23.4036136619),
    (-47.10472222200, -23.2402777780),
    (-47.25192067260, -23.1347915266),
    (-47.39888888900, -23.0291666670),
    (-47.40531214760, -23.0069348209),
    (-47.40377565800, -22.9807166225),
    (-47.39928886810, -22.9547905659),
    (-47.39190255780, -22.9294404543),
    (-47.38169912370, -22.9049436329),
    (-47.36879161300, -22.8815679684),
    (-47.35332243130, -22.8595689372),
    (-47.33546173970, -22.8391868539),
    (-47.31540556250, -22.8206442696),
    (-47.29337362520, -22.8041435665),
    (-47.26960694870, -22.7898647741),
    (-47.24436522530, -22.7779636293),
    (-47.21792400390, -22.7685699005),
    (-47.17722222200, -22.7633333330)
]

# TMA São Paulo 1's vertical limits
tma1_upper_limit = 24500
tma1_lower_limit = 5500

# List of points delimiting TMA São Paulo 1's horizontal limits
tma1_coords = [
    (-045.38082500, -23.88307500),
    (-045.55586670, -23.25037780),
    (-045.61360000, -23.04041944),
    (-045.66710830, -23.05229444),
    (-045.92609170, -22.97498890),
    (-046.12291390, -22.55789720),
    (-046.98529170, -22.46140560),
    (-047.56018890, -22.69492780),
    (-047.68771110, -22.93983330),
    (-047.80167500, -23.25763330),
    (-047.73306390, -23.62205280),
    (-046.69168610, -24.40681670),
    (-046.16711110, -24.30751940),
    (-046.07171944, -24.07566111),
    (-045.38082500, -23.88307500),
]


def point_in_airspace(position_coords: list,
                      position_alt: float,
                      airspace_lower_limit: float,
                      airspace_upper_limit: float,
                      airspace_horizontal_limits: list) -> bool:
    """
Given a position (latitude, longitude and altitude) and an airspace's vertical
and horizontal limits, returns whether the point is contained within the
airspace or not

    :param position_coords: (latitude, longitude) in decimal format
    :param position_alt: position altitude in feet
    :param airspace_lower_limit: airspace lower vertical limit in feet
    :param airspace_upper_limit: airspace upper vertical limit in feet
    :param airspace_horizontal_limits: list of latitude and longitude
           coordinates that horizontally limits the airspace
    :return: True/False, whether the position is contained within the airspace
             or not
    """
    horizontal_limits = Polygon(airspace_horizontal_limits)
    point = Point(position_coords[1], position_coords[0])

    is_within_vertical_limits = \
        airspace_lower_limit < position_alt <= airspace_upper_limit
    is_within_horizontal_limits = \
        horizontal_limits.contains(point) or horizontal_limits.touches(point)

    return is_within_horizontal_limits and is_within_vertical_limits


def get_flight_time(whole_data: list,
                    tma1_data: list,
                    tma2_data: list,
                    ctr_data: list) -> dict:

    for i in range(len(whole_data) - 1):
        obs1_time = \
            datetime.datetime.fromtimestamp(time.mktime(whole_data[i][0]))
        obs2_time = \
            datetime.datetime.fromtimestamp(time.mktime(whole_data[i + 1][0]))

        time_variation = obs2_time - obs1_time
        time_variation = time_variation.total_seconds()/60

        altitude_variation = whole_data[i + 1][4] - whole_data[i][4]

        rate_of_climb = round(altitude_variation / time_variation)

        whole_data[i].append(rate_of_climb)

    obs1_time = datetime.datetime.fromtimestamp(time.mktime(whole_data[-2][0]))
    obs2_time = datetime.datetime.fromtimestamp(time.mktime(whole_data[-1][0]))

    time_variation = obs2_time - obs1_time
    time_variation = time_variation.total_seconds()/60

    altitude_variation = whole_data[-2][4] - whole_data[-1][4]

    rate_of_climb = round(altitude_variation / time_variation)

    whole_data[-1].append(rate_of_climb)

    pitch = None
    mean_tendency = None
    for i in range(len(whole_data) - 5):
        rate_of_climb = [whole_data[i + j][7] for j in range(5)]
        mean_rate_of_climb = round(sum(rate_of_climb)/5)

        if -20 < mean_rate_of_climb < 20:
            mean_tendency = 'cruise'

        elif mean_rate_of_climb > 100:
            mean_tendency = 'climb'

        elif mean_rate_of_climb < -100:
            mean_tendency = 'descent'

        if whole_data[i][4] == 0 and whole_data[i][5] == 0:
            pitch = 'parked'

        elif whole_data[i][4] == 0 and whole_data[i][5] < 30:
            pitch = 'taxi'

        elif i < len(whole_data) \
                and whole_data[i][4] == 0 \
                and (whole_data[i - 1][8] == 'taxi'
                     or whole_data[i - 1][8] == 'takeoff'):
            pitch = 'takeoff'

        elif whole_data[i][4] == 0 \
                and (whole_data[i - 1][8] == 'descent'
                     or whole_data[i - 1][8] == 'descent_step'
                     or whole_data[i - 1][8] == 'landing'):
            pitch = 'landing'

        elif i > 1 \
                and (whole_data[i - 1][8] == 'descent'
                     or whole_data[i - 1][8] == 'descent_step') \
                and abs(whole_data[i][7]) < 50:
            pitch = 'descent_step'

        elif mean_tendency == 'cruise' and abs(whole_data[i][7]) < 50:
            pitch = 'cruise'

        elif mean_tendency == 'climb' and whole_data[i][7] > 50:
            pitch = 'climb'

        elif mean_tendency == 'descent' and whole_data[i][7] < -50:
            pitch = 'descent'

        whole_data[i].append(pitch)

    for i in range(len(whole_data)-5, len(whole_data)):
        rate_of_climb = [whole_data[i - j][7] for j in range(5)]
        mean_rate_of_climb = round(sum(rate_of_climb)/5)

        if -20 < mean_rate_of_climb < 20:
            mean_tendency = 'cruise'

        elif mean_rate_of_climb > 100:
            mean_tendency = 'climb'

        elif mean_rate_of_climb < -100:
            mean_tendency = 'descent'

        if whole_data[i][4] == 0 and whole_data[i][5] == 0:
            pitch = 'parked'

        elif whole_data[i][4] == 0 and whole_data[i][5] < 30:
            pitch = 'taxi'

        elif i < len(whole_data) \
                and whole_data[i][4] == 0 \
                and (whole_data[i - 1][8] == 'taxi'
                     or whole_data[i - 1][8] == 'takeoff'):
            pitch = 'takeoff'

        elif whole_data[i][4] == 0 \
                and (whole_data[i - 1][8] == 'descent'
                     or whole_data[i - 1][8] == 'descent_step'
                     or whole_data[i - 1][8] == 'landing'):
            pitch = 'landing'

        elif i > 1 \
                and (whole_data[i - 1][8] == 'descent'
                     or whole_data[i - 1][8] == 'descent_step') \
                and abs(whole_data[i][7]) < 50:
            pitch = 'descent_step'

        elif mean_tendency == 'cruise' and abs(whole_data[i][7]) < 50:
            pitch = 'cruise'

        elif mean_tendency == 'climb' and whole_data[i][7] > 50:
            pitch = 'climb'

        elif mean_tendency == 'descent' and whole_data[i][7] < -50:
            pitch = 'descent'

        whole_data[i].append(pitch)

    liftoff_index = 0
    for i in range(len(whole_data)):
        if whole_data[i][4] > 0:
            liftoff_index = i
            break

    liftoff_previous_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[liftoff_index - 1][0])
    )
    liftoff_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[liftoff_index][0])
    )

    liftoff_time_error = liftoff_time - liftoff_previous_time

    level_off_index = None
    for i in range(len(whole_data)):
        if whole_data[i][8] == 'cruise':
            level_off_index = i
            break

    level_off_previous_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[level_off_index - 1][0])
    )
    level_off_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[level_off_index][0])
    )

    level_off_time_error = level_off_time - level_off_previous_time

    descent_index = None
    for i in range(len(whole_data)):
        if whole_data[i][8] == 'descent':
            descent_index = i
            break

    descent_previous_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[descent_index - 1][0])
    )

    descent_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[descent_index][0])
    )

    descent_time_error = descent_time - descent_previous_time

    landing_index = None
    for i in range(len(whole_data)-1, -1, -1):
        if whole_data[i][8] == 'landing' and whole_data[i-1][8] != 'landing':
            landing_index = i
            break
    landing_previous_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[landing_index - 1][0])
    )

    landing_time = datetime.datetime.fromtimestamp(
        time.mktime(whole_data[landing_index][0])
    )

    landing_time_error = landing_time - landing_previous_time

    first_entry_time = datetime.datetime.fromtimestamp(time.mktime(whole_data[0][0])) \
        if (whole_data[0][8] == 'parked' or whole_data[0][8] == 'taxi') else None

    before_takeoff_duration = liftoff_time - first_entry_time if first_entry_time is not None else None

    tma1_time = datetime.timedelta(0)
    tma1_time_error = datetime.timedelta(0)
    interrupted_index = list()
    for j in range(len(tma1_data) - 1):
        if tma1_data[j][2] == (tma1_data[j + 1][2] - 1):
            tma1_time += (
                datetime.datetime.fromtimestamp(time.mktime(tma1_data[j + 1][0]))
                - datetime.datetime.fromtimestamp(time.mktime(tma1_data[j][0]))
            )

        else:
            interrupted_index.append(tma1_data[j][2])

    for index in interrupted_index:
        tma1_time_error += (
            datetime.datetime.fromtimestamp(time.mktime(whole_data[index + 1][0]))
            - datetime.datetime.fromtimestamp(time.mktime(whole_data[index][0]))
        )

    tma1_time_error += (
        datetime.datetime.fromtimestamp(time.mktime(tma1_data[0][0]))
        - datetime.datetime.fromtimestamp(time.mktime(whole_data[tma1_data[0][2] - 1][0]))
    )

    tma1_time_error += (
        datetime.datetime.fromtimestamp(time.mktime(whole_data[tma1_data[-1][2] + 1][0]))
        - datetime.datetime.fromtimestamp(time.mktime(tma1_data[-1][0]))
    )

    tma2_time = datetime.timedelta(0)
    tma2_time_error = datetime.timedelta(0)
    interrupted_index.clear()
    for j in range(len(tma2_data) - 1):
        if tma2_data[j][2] == (tma2_data[j + 1][2] - 1):
            tma2_time += (
                datetime.datetime.fromtimestamp(time.mktime(tma2_data[j + 1][0]))
                - datetime.datetime.fromtimestamp(time.mktime(tma2_data[j][0]))
            )

        else:
            interrupted_index.append(tma2_data[j][2])

    for index in interrupted_index:
        tma2_time_error += (
            datetime.datetime.fromtimestamp(time.mktime(whole_data[index + 1][0]))
            - datetime.datetime.fromtimestamp(time.mktime(whole_data[index][0]))
        )

    tma2_time_error += (
            datetime.datetime.fromtimestamp(time.mktime(tma2_data[0][0]))
            - datetime.datetime.fromtimestamp(time.mktime(whole_data[tma2_data[0][2] - 1][0]))
    )

    tma2_time_error += (
            datetime.datetime.fromtimestamp(
                time.mktime(whole_data[tma2_data[-1][2] + 1][0]))
            - datetime.datetime.fromtimestamp(time.mktime(tma2_data[-1][0]))
    )

    ctr_time = datetime.timedelta(0)
    ctr_time_error = datetime.timedelta(0)
    interrupted_index.clear()
    for j in range(len(ctr_data) - 1):
        if ctr_data[j][2] == (ctr_data[j + 1][2] - 1):
            ctr_time += (
                datetime.datetime.fromtimestamp(time.mktime(ctr_data[j + 1][0]))
                - datetime.datetime.fromtimestamp(time.mktime(ctr_data[j][0]))
            )

        else:
            interrupted_index.append(ctr_data[j][2])

    for index in interrupted_index:
        ctr_time_error += (
            datetime.datetime.fromtimestamp(time.mktime(whole_data[index + 1][0]))
            - datetime.datetime.fromtimestamp(time.mktime(whole_data[index][0]))
        )

    ctr_time_error += (
            datetime.datetime.fromtimestamp(time.mktime(ctr_data[0][0]))
            - datetime.datetime.fromtimestamp(
        time.mktime(whole_data[ctr_data[0][2] - 1][0]))
    )

    ctr_time_error += (
            datetime.datetime.fromtimestamp(
                time.mktime(whole_data[ctr_data[-1][2] + 1][0]))
            - datetime.datetime.fromtimestamp(time.mktime(ctr_data[-1][0]))
    )

    after_landing_ground_time = (
        datetime.datetime.fromtimestamp(time.mktime(whole_data[-1][0]))
        - landing_time
    )

    total_time = (
        datetime.datetime.fromtimestamp(time.mktime(whole_data[-1][0]))
        - datetime.datetime.fromtimestamp(time.mktime(whole_data[0][0]))
    )

    flight_time = total_time - (before_takeoff_duration + after_landing_ground_time)

    non_tma_ctr_time = total_time - (tma1_time + tma2_time + ctr_time)
    non_tma_ctr_time_error = tma1_time_error + tma2_time_error + ctr_time_error

    return {
        'takeoff_time': liftoff_time,
        'takeoff_time_error': liftoff_time_error,
        'level_off_time': level_off_time,
        'level_off_time_error': level_off_time_error,
        'descent_init_time': descent_time,
        'descent_init_time_error': descent_time_error,
        'touchdown_time': landing_time,
        'touchdown_time_error': landing_time_error,

        'recorded_time': total_time,
        'ground_time': before_takeoff_duration + after_landing_ground_time,
        'ground_time_error': liftoff_time_error + landing_time_error,
        'flight_time': flight_time,
        'flight_time_error': liftoff_time_error + landing_time_error,
        'before_takeoff_ground_duration': before_takeoff_duration,
        'before_takeoff_ground_duration_error': liftoff_time_error,
        'climb_duration': level_off_time - liftoff_time,
        'climb_duration_error': level_off_time_error + liftoff_time_error,
        'cruise_duration': descent_time - level_off_time,
        'cruise_duration_error': level_off_time_error + descent_time_error,
        'descent_duration': landing_time - descent_time,
        'descent_duration_error': descent_time_error + landing_time_error,
        'after_landing_ground_duration': after_landing_ground_time,
        'after_landing_ground_duration_error': landing_time_error,

        'outside_tma_ctr': non_tma_ctr_time,
        'outside_tma_ctr_error': non_tma_ctr_time_error,
        'inside_tma_sao_paulo1': tma1_time,
        'inside_tma_sao_paulo1_error': tma1_time_error,
        'inside_tma_sao_paulo2': tma2_time,
        'inside_tma_sao_paulo2_error': tma2_time_error,
        'inside_ctr_campinas': ctr_time,
        'inside_ctr_campinas_error': ctr_time_error,
        'after_landing_ground_time': after_landing_ground_time,
        'after_landing_ground_time_error': landing_time_error,
    }


# Read the file containing the flight tracking data
with open(tracking_filepath, 'r') as file_handle:
    reader = csv.reader(file_handle)
    data = [line for line in reader]

# Delete CSV header
del data[0]

for i in range(len(data)):
    # Convert timestamp to time struct
    data[i][0] = time.gmtime(int(data[i][0]))
    # Add index information
    data[i][2] = i
    # Split latitude and longitude information
    data[i][3] = str(data[i][3]).split(',')
    # Cast latitude and longitude as float
    data[i][3][0] = float(data[i][3][0])
    data[i][3][1] = float(data[i][3][1])
    # Cast altitude as float
    data[i][4] = float(data[i][4])
    # Cast speed as float
    data[i][5] = float(data[i][5])
    # Add index

# Ground movement
ground_movement = list(filter(lambda x: x[4] == 0, data))

# Filter ground movement
non_tma = list(filter(lambda x: x[4] != 0, data))

# Filter points inside TMA São Paulo 1
non_tma = list(filter(
    lambda x: not point_in_airspace(x[3], x[4],
                                    tma1_lower_limit,
                                    tma1_upper_limit,
                                    tma1_coords),
    non_tma))
# Filter points inside TMA São Paulo 2
non_tma = list(filter(lambda x: not point_in_airspace(x[3], x[4],
                                                      tma2_lower_limit,
                                                      tma2_upper_limit,
                                                      tma2_coords),
                      non_tma))
# Filter points inside CTR Campinas
non_tma = list(filter(lambda x: not point_in_airspace(x[3], x[4],
                                                      ctr_lower_limit,
                                                      ctr_upper_limit,
                                                      ctr_coords),
                      non_tma))

# Get points inside TMA São Paulo 1
on_tma1 = list(filter(lambda x: point_in_airspace(x[3], x[4],
                                                  tma1_lower_limit,
                                                  tma1_upper_limit,
                                                  tma1_coords),
                      data))
# Get points inside TMA São Paulo 2
on_tma2 = list(filter(lambda x: point_in_airspace(x[3], x[4],
                                                  tma2_lower_limit,
                                                  tma2_upper_limit,
                                                  tma2_coords),
                      data))
# Get Points inside CTR Campinas
on_ctr = list(filter(lambda x: point_in_airspace(x[3], x[4],
                                                 ctr_lower_limit,
                                                 ctr_upper_limit,
                                                 ctr_coords),
                     data))

flight_time_stats = get_flight_time(data, on_tma1, on_tma2, on_ctr)

# Visualization - Set figure size and ax limits
fig, ax = plt.subplots()
fig.set_size_inches(16, 9)
fig.subplots_adjust(wspace=0.01)
fig.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.98)
ax.set_xlim(-48, -45)
ax.set_ylim(-25, -22)

# Visualization - Plot runway
rwy = ax.plot(rwy_thr_xs, rwy_thr_ys, 'k-', zorder=3, alpha=0.5)

# Visualization - Create patch for CTR Campinas
patch = patches.PathPatch(
    Path(ctr_coords, closed=True),
    lw=0.5, linestyle='--', alpha=0.5
)
# Visualization - Create patch for TMA São Paulo 1
patch2 = patches.PathPatch(
    Path(tma1_coords, closed=True),
    lw=0.5, linestyle='--', alpha=0.5
)
# Visualization - Create patch for TMA São Paulo 2
patch3 = patches.PathPatch(
    Path(tma2_coords, closed=True),
    lw=0.5, linestyle='--', alpha=0.5
)

# Visualization - Add created patches to chart
ax.add_patch(patch)
ax.add_patch(patch2)
ax.add_patch(patch3)

# Visualization - Get coordinates of ground movements
ground_movement_xs = [entry[3][1] for entry in ground_movement]
ground_movement_ys = [entry[3][0] for entry in ground_movement]
# Visualization - Get coordinates of position in airspace
#                 other than TMAs São Paulo and CTR Campinas
non_tma_xs = [entry[3][1] for entry in non_tma]
non_tma_ys = [entry[3][0] for entry in non_tma]
# Visualization - Get coordinates of positions inside TMA São Paulo 1
on_tma1_xs = [entry[3][1] for entry in on_tma1]
on_tma1_ys = [entry[3][0] for entry in on_tma1]
# Visualization - Get coordinates of positions inside TMA São Paulo 2
on_tma2_xs = [entry[3][1] for entry in on_tma2]
on_tma2_ys = [entry[3][0] for entry in on_tma2]
# Visualization - Get coordinates of positions inside CTR Campinas
on_ctr_xs = [entry[3][1] for entry in on_ctr]
on_ctr_ys = [entry[3][0] for entry in on_ctr]

# Visualization - Plot all positions reported by the aircraft
ax.plot(non_tma_xs, non_tma_ys, 'bo', alpha=0.5)
ax.plot(on_tma1_xs, on_tma1_ys, 'co', alpha=0.5)
ax.plot(on_tma2_xs, on_tma2_ys, 'ro', alpha=0.5)
ax.plot(on_ctr_xs, on_ctr_ys, 'mo', alpha=0.5)
ax.plot(ground_movement_xs, ground_movement_ys, 'go', alpha=0.5)

# Visualization - Display figure
fig.gca().set_position([0, 0, 1, 1])
fig.savefig("test.svg")
# fig.show()
print()
