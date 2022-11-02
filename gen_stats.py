import datetime
from metar import Metar
import re
import pandas as pd

procs = ['VFR', 'VFR-E', 'IFR-ILS', 'IFR-LNAV/VNAV', 'IFR-LNAV-PAB',
         'IFR-LNAV-PCD', 'IFR-RNP030', 'IFR-RNP015']

def check_ops(op: str, metar: Metar.Metar) -> bool:
    ceiling_minimum = None
    visibility_minimum = None

    if op.upper() == 'VFR':
        ceiling_minimum = 1500
        visibility_minimum = 5000

    elif op.upper() == 'VFR-E':
        ceiling_minimum = 1000
        visibility_minimum = 3000



    else:
        if metar.wind_speed is not None:
            wind_speed = metar.wind_speed.value('kt')

        else:
            wind_speed = None

        if metar.wind_dir is not None:
            wind_dir = metar.wind_dir.value()
        else:
            wind_dir = None

        # RWY 15 in use
        if wind_speed is None or \
                wind_speed < 6 or \
                wind_dir is None or \
                (abs(wind_dir - 149) > abs(wind_dir - 239)):

            if op.upper() == 'IFR-ILS':
                ceiling_minimum = 200
                visibility_minimum = 800

            elif op.upper() == 'IFR-LNAV/VNAV':
                ceiling_minimum = 357
                visibility_minimum = 1100

            elif op.upper() == 'IFR-LNAV-PAB':
                ceiling_minimum = 430
                visibility_minimum = 800

            elif op.upper() == 'IFR-LNAV-PCD':
                ceiling_minimum = 430
                visibility_minimum = 1500

            elif op.upper() == 'IFR-RNP030':
                ceiling_minimum = 339
                visibility_minimum = 1000

            elif op.upper() == 'IFR-RNP015':
                ceiling_minimum = None
                visibility_minimum = None

        # RWY 33 in use
        else:
            if op.upper() == 'IFR-LNAV/VNAV':
                ceiling_minimum = 363
                visibility_minimum = 1700

            elif op.upper() == 'IFR-LNAV-PAB':
                ceiling_minimum = 450
                visibility_minimum = 1700

            elif op.upper() == 'IFR-LNAV-PCD':
                ceiling_minimum = 450
                visibility_minimum = 2100

            elif op.upper() == 'IFR-RNP030':
                ceiling_minimum = 363
                visibility_minimum = 1700

            elif op.upper() == 'IFR-RNP015':
                ceiling_minimum = 250
                visibility_minimum = 1300

            elif op.upper() == 'IFR-ILS':
                ceiling_minimum = None
                visibility_minimum = None

    if ceiling_minimum is None and visibility_minimum is None:
        return False

    if ceiling_minimum is None or visibility_minimum is None:
        raise ValueError('Operation type not found')

    ceiling_heights = []
    for layer in metar.sky:
        if layer[0].upper() in {'BKN', 'OVC'}:
            ceiling_heights.append(layer[1].value('ft'))

    if len(ceiling_heights) > 0 and min(ceiling_heights) < ceiling_minimum:
        return False

    visibilities = []
    if metar.vis is not None:
        visibilities.append(metar.vis.value('m'))

    if metar.max_vis is not None:
        visibilities.append(metar.max_vis.value('m'))

    for vis in metar.runway:
        visibilities.append(vis[1].value('m'))

    if len(visibilities) > 0 and min(visibilities) < visibility_minimum:
        return False

    return True


daily_stats = dict()
start_date = datetime.datetime(day=1, month=8, year=2022, hour=0, minute=0)
end_date = datetime.datetime(day=30, month=10, year=2022, hour=0, minute=1)

# Create data structure
current_date = start_date
while current_date < end_date:
    key = current_date.strftime("%d/%m/%Y")
    daily_stats[key] = dict()
    daily_stats[key]["hourly_stats"] = dict()
    for i in range(24):
        key2 = f'{i:02}'
        daily_stats[key]["hourly_stats"][key2] = {
            "obs": {
                "raw_obs": list(),
                "parsed_obs": dict(),
                "obs_duration": list(),
            },
            "no_info_time": datetime.timedelta(0),
            "33_inuse_time": datetime.timedelta(0),
            "15_inuse_time": datetime.timedelta(0),
            "unavailable_VFR_time": datetime.timedelta(0),
            "unavailable_VFR-E_time": datetime.timedelta(0),
            "unavailable_IFR-ILS_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV/VNAV_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV-PAB_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV-PCD_time": datetime.timedelta(0),
            "unavailable_IFR-RNP030_time": datetime.timedelta(0),
            "unavailable_IFR-RNP015_time": datetime.timedelta(0),
        }

    current_date += datetime.timedelta(days=1)

with open('data/sbkp.txt', 'r', encoding='utf8') as file_handle:
    data = file_handle.readlines()

for line in data:
    timetag = line.strip('\ufeff')[:10]
    year = int(timetag[:4])
    month = int(timetag[4:6])
    day = int(timetag[6:8])
    hour = int(timetag[8:10])

    key1 = f"{day:02}/{month:02}/{year}"
    key2 = f"{hour:02}"

    raw_metar = line[13:].strip()

    daily_stats[key1]["hourly_stats"][key2]["obs"]["raw_obs"].append(raw_metar)


current_date = start_date
while current_date < end_date:
    key1 = current_date.strftime("%d/%m/%Y")
    for i in range(24):
        key2 = f'{i:02}'
        n_obs = len(daily_stats[key1]["hourly_stats"][key2]["obs"]['raw_obs'])

        if n_obs > 0:
            for j in range(n_obs):
                # Parse the METAR information
                if "/////CB" not in daily_stats[key1]["hourly_stats"][key2]["obs"]['raw_obs'][j]:
                    parsed_obs = Metar.Metar(
                        daily_stats[key1]["hourly_stats"][key2]["obs"]['raw_obs'][j]
                    )
                    daily_stats[key1]["hourly_stats"][key2]["obs"][
                        'parsed_obs'][parsed_obs.time.minute] = parsed_obs

                # /////CB in METAR
                # Assigns None to its place in the parsed_metar dict
                else:
                    info_minute = re.search(
                        r'\d{4}(?P<min>\d{2})Z',
                        daily_stats[key1]["hourly_stats"][key2]["obs"]['raw_obs'][j]
                    )['min']
                    daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"
                                                   ][int(info_minute)] = None

            # Recalculate number of observations
            # In case there are duplicate metar information
            n_obs = len(daily_stats[key1]["hourly_stats"][key2]["obs"]['parsed_obs'])

            # Compile the time, in minutes, of the observations
            obs_minutes = list(
                daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"].keys()
            )

            # Calculate the duration of the observations
            for j in range(n_obs - 1):
                daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"].append(
                    datetime.timedelta(minutes=(
                        obs_minutes[j+1] - obs_minutes[j]
                    ))
                )

            # Calculate the duration of the last observation
            daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"].append(
                datetime.timedelta(minutes=(60 - obs_minutes[-1]))
            )

            # Calculate active runway times
            for j in range(n_obs):
                if daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"][obs_minutes[j]] \
                        is not None:

                    if daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"][obs_minutes[j]].wind_speed is not None:
                        wind_speed = daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"][obs_minutes[j]].wind_speed.value('kt')

                    else:
                        wind_speed = None

                    if daily_stats[key1]["hourly_stats"][key2]["obs"][
                            "parsed_obs"][obs_minutes[j]].wind_dir is not None:
                        wind_dir = daily_stats[key1]["hourly_stats"][key2]["obs"][
                            "parsed_obs"][obs_minutes[j]].wind_dir

                    else:
                        wind_dir = None

                    if wind_speed is None or\
                            wind_speed < 6 or \
                            wind_dir is None or \
                            (abs(wind_dir.value() - 149) > abs(
                                wind_dir.value() - 239)):
                        daily_stats[key1]["hourly_stats"][key2]["15_inuse_time"] += \
                            daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"][j]

                    else:
                        daily_stats[key1]["hourly_stats"][key2]["33_inuse_time"] += \
                            daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"][j]

            # Calculate unavailable times
            for j in range(n_obs):
                # Cases where there's /////CB on METAR
                if daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"][obs_minutes[j]]\
                        is None:

                    for proc in procs:
                        daily_stats[key1]["hourly_stats"][key2][f"unavailable_{proc}_time"] += \
                            daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"][j]


                # Cases where is a valid parsed METAR
                else:
                    for proc in procs:
                        if not check_ops(
                                proc,
                                daily_stats[key1]["hourly_stats"][key2]["obs"]["parsed_obs"][obs_minutes[j]]
                        ):
                            daily_stats[key1]["hourly_stats"][key2][f"unavailable_{proc}_time"] += \
                                daily_stats[key1]["hourly_stats"][key2]["obs"]["obs_duration"][j]

        # There's no metar information for that hour
        else:
            daily_stats[key1]["hourly_stats"][key2]["no_info_time"] += \
                datetime.timedelta(hours=1)

    no_info_time = datetime.timedelta(0)
    r15_inuse_time = datetime.timedelta(0)
    r33_inuse_time = datetime.timedelta(0)
    for j in range(24):
        no_info_time += \
            daily_stats[key1]["hourly_stats"][f'{j:02}']['no_info_time']
        r15_inuse_time += \
            daily_stats[key1]["hourly_stats"][f'{j:02}']['15_inuse_time']
        r33_inuse_time += \
            daily_stats[key1]["hourly_stats"][f'{j:02}']['33_inuse_time']

    daily_stats[key1]['no_info_time'] = no_info_time
    daily_stats[key1]['15_inuse_time'] = r15_inuse_time
    daily_stats[key1]['33_inuse_time'] = r33_inuse_time

    for proc in procs:
        unavailable_proc_time = datetime.timedelta(0)
        for j in range(24):
            unavailable_proc_time += \
                daily_stats[key1]["hourly_stats"][f'{j:02}'][f'unavailable_{proc}_time']

        daily_stats[key1][f'unavailable_{proc}_time'] = unavailable_proc_time

    current_date += datetime.timedelta(days=1)

month_stats = dict()

# Create data structure
current_date = start_date
while current_date < end_date:
    month_key = current_date.strftime("%m/%Y")
    day_key = current_date.strftime("%d/%m/%Y")

    if month_key not in month_stats:
        month_stats[month_key] = {
            "no_info_time": datetime.timedelta(0),
            "33_inuse_time": datetime.timedelta(0),
            "15_inuse_time": datetime.timedelta(0),
            "unavailable_VFR_time": datetime.timedelta(0),
            "unavailable_VFR-E_time": datetime.timedelta(0),
            "unavailable_IFR-ILS_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV/VNAV_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV-PAB_time": datetime.timedelta(0),
            "unavailable_IFR-LNAV-PCD_time": datetime.timedelta(0),
            "unavailable_IFR-RNP030_time": datetime.timedelta(0),
            "unavailable_IFR-RNP015_time": datetime.timedelta(0),
        }

    del daily_stats[day_key]['hourly_stats']
    for key in daily_stats[day_key]:
        month_stats[month_key][key] += \
            daily_stats[day_key][key]

    current_date += datetime.timedelta(days=1)

labels = {
    "no_info_time": 'Tempo sem informações válidas',
    "33_inuse_time": 'Tempo que a pista 33 esteve em uso',
    "15_inuse_time": 'Tempo que a pista 15 esteve em uso',
    "unavailable_VFR_time": 'Tempo que o aeródromo não recebeu operações VFR',
    "unavailable_VFR-E_time": 'Tempo que o aeródromo não recebeu operações VFR especial',
    "unavailable_IFR-ILS_time": 'Tempo que o aeródromo não recebeu operações ILS',
    "unavailable_IFR-LNAV/VNAV_time": 'Tempo que o aeródromo não recebeu operações LNAV/VNAV',
    "unavailable_IFR-LNAV-PAB_time": 'Tempo que o aeródromo não recebeu operações LNAV (Performance A e B)',
    "unavailable_IFR-LNAV-PCD_time": 'Tempo que o aeródromo não recebeu operações LNAV (Performance C e D)',
    "unavailable_IFR-RNP030_time": 'Tempo que o aeródromo não recebeu operações RNP 0.3',
    "unavailable_IFR-RNP015_time": 'Tempo que o aeródromo não recebeu operações RNP 0.15',
}

d = pd.DataFrame.from_dict(daily_stats, orient='index').rename(columns=labels)
m = pd.DataFrame.from_dict(month_stats, orient='index').rename(columns=labels)

d.to_excel('estatisticas diárias 2.xlsx')
m.to_excel('estatisticas mensais 2.xlsx')
print()
