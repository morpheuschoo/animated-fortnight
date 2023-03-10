import pandas as pd
from ujson import load
import datetime
import re

# loads in ME/ADW google sheet and returns it as a dataframe
def csv_to_dataframe(month_num, year, thing):
    
    month_alpha_ref = ["JAN", "FEB", "MAR", "APR", "MAY", "JUNE", "JULY", "AUGUST", "SEPT", "OCT", "NOV", "DEC"]

    # converts months in numbers to months in aphabets
    month_alpha = month_alpha_ref[month_num - 1]

    if thing == 'ME':
        return pd.read_csv(f"https://docs.google.com/spreadsheets/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/gviz/tq?tqx=out:csv&sheet={month_alpha}%2020{year}").fillna('NIL')
    
    elif thing == 'ADW':
        return pd.read_csv(f"https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/gviz/tq?tqx=out:csv&sheet={month_alpha}%20{year}").fillna('NIL')

def open_sheet(DATE, thing):
    
    # splitting [DD][MM][YY], removing trailing zeros and converting it into integers
    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')
    
    MONTH = int(date_datetime.strftime('%#m'))
    YEAR = int(date_datetime.strftime('%#y'))

    # trys to open csv sheet in storage
    # if sheet does not exist, download sheet from online and use it
    if thing == 'ME':
        try:
            return pd.read_csv(f'online_sheets/ME/ME_{MONTH}({YEAR}).csv')
        except:
            return csv_to_dataframe(MONTH, YEAR, thing)
    
    if thing == 'ADW':
        try:
            return pd.read_csv(f'online_sheets/ADW/ADW_{MONTH}({YEAR}).csv')
        except:
            return csv_to_dataframe(MONTH, YEAR, thing)

# function to load in everyone and return a list
def load_163():
    
    # load in all external files as a list
    with open('flight_personnel/ALPHA.json') as alpha_json:
        alpha_list = load(alpha_json)

    with open('flight_personnel/BRAVO.json') as bravo_json:
        bravo_list = load(bravo_json)

    with open('flight_personnel/OTHERS.json') as others_json:
        others_list = load(others_json)

    # assigning flight to personnel
    def update_flight(flight_dict, flight):
        for x in flight_dict:
            x['FLIGHT'] = flight

    update_flight(alpha_list, 'ALPHA')
    update_flight(bravo_list, 'BRAVO')
    update_flight(others_list, 'OTHERS')

    everyone_list = []

    # merging alpha, bravo and others into one list called everyone
    everyone_list.extend(alpha_list + bravo_list + others_list)

    return everyone_list

# function to update everyone list
def update(main_column, condition, edit_column, value):
    
    global everyone_list
    
    for x in everyone_list:
        if x[main_column] == condition:
            x[edit_column] = value

# [DD][MM][YY] to datetime converter
def datetime_convert(DATE):
    return datetime.datetime.strptime(DATE, '%d%m%y')

# loads in ME sheet and assigns statuses to each person
# status taken from ME sheet
def load_ME_sheet(DATE):

    global everyone_list

    # loads in everyone from alpha, bravo and others
    # includes rank, name in ME, displayed name, flight and whether the personnel is a regular or NSF
    everyone_list = load_163()

    # obtain DAY from DATE
    date_datetime = datetime_convert(DATE)
    DAY = int(date_datetime.strftime('%#d'))

    # loading in all external files into code as a dictionary/list
    with open('references/callsign_ref.json') as callsign_ref_json:
        callsign_ref_dict = load(callsign_ref_json)

    with open('references/rank_sorting.json') as rank_sorting_json:
        rank_sorting_dict = load(rank_sorting_json)
    
    with open('override/override_ps.json') as override_ps_json:
        override_ps_list = load(override_ps_json)
    
    with open('override/merged_cells.json') as merged_cells_json:
        merged_cells_list = load(merged_cells_json)

    # load in ME sheet
    ME_df = open_sheet(DATE, 'ME')

    # assign UNKNOWN status to everyone
    for x in everyone_list:
        x['STATUS_IN_PS'] = 'UNKNOWN'

    # assign present(NIL) status to those not in ME_df (eg OC, ...)
    for x in callsign_ref_dict.values():
        update('NAME_IN_PS', x, 'STATUS_IN_PS', 'NIL')
    
    # assign status to personnel
    # status taken from ME sheet
    # leading and trailing whitespaces removed from name and status
    # if / present leading and trailing whitespaces also removed
    for x in range(9, len(ME_df) - 33):
        if ME_df.iloc[x, 0] != 'NIL':
            update('NAME_IN_PS', ME_df.iloc[x, 0].upper().strip(), 'STATUS_IN_PS', re.sub('\s*/\s*', '/', ME_df.iloc[x, DAY].upper().strip()))
    
    # function that does the override
    def update_from_list(list_in_question):
        for x in list_in_question:
            if datetime_convert(x['START_DATE']) <= datetime_convert(DATE) <= datetime_convert(x['END_DATE']):
                update('NAME_IN_PS', x['NAME_IN_PS'], 'STATUS_IN_PS', x['STATUS_IN_PS'])
    
    # adds in the merged cells
    # CSV does not contain the merged cells
    update_from_list(merged_cells_list)

    # HIGHEST PRIORITY
    # override that is manually inputted
    update_from_list(override_ps_list)
    
    # assign everyone a number to their rank for easy sorting
    for x in rank_sorting_dict:
        update('RANK', x, 'RANK_SORT', rank_sorting_dict[x])

def load_standby_and_duty():

    global everyone_list

    def sort_by_rank(temp_list):

        # remove personnel from list who do not have a rank
        for x in temp_list:
            if x['RANK_SORT'] == 100:
                temp_list.remove(x)

        # sort list by rank
        # highest rank at the front, lowest rank at the back
        temp_list.sort(key=lambda x: x.get('RANK_SORT'), reverse=True)
    
        return temp_list
    
    # each role(key) corresponds to the min(value[0]) and max(value[1])
    duty_list_ran_ref = {
        0: [9, 12],
        1: [5, 9],
        2: [2, 9],
        3: [2, 9],
        4: [1, 3],
        5: [1, 3]
    }

    # sort personnel on duty by rank
    duty_list = sort_by_rank([x for x in everyone_list if x['STATUS_IN_PS'] == 'X'])

    # declare a duty list that contains the rank and name of personnel
    # fill list with 6 UNKNOWN which ensures that the length of the list is excatly 6
    duty_list_ran = ['UNKNOWN' for x in range(6)]

    # placing rank and name into duty list
    # ensures that role and rank match
    i = 0
    check = []
    for j in range(6):
        if duty_list[i]['RANK_SORT'] in range(duty_list_ran_ref[j][0], duty_list_ran_ref[j][1]) and not duty_list[i]['NAME_IN_PS'] in check:
            duty_list_ran[j] = f'{duty_list[i]["RANK"]} {duty_list[i]["DISPLAY_NAME"]}'
            check.append(duty_list[i]['NAME_IN_PS'])
            i += 1 if i < len(duty_list) - 1 else 0
    
    # each role(key) corresponds to the min(value[0]) rank and max(value[1]) rank
    standby_list_ran_ref = {
        0: [9, 12],
        1: [2, 9],
        2: [1, 3]
    }

    # sort personnel on standby by rank
    standby_list = sort_by_rank([x for x in everyone_list if 'SB' in x['STATUS_IN_PS']])

    # declare a standby list that contains the rank and name of personnel
    # fill list with 3 UNKNOWN which ensures that the length of the list is exactly 3
    standby_list_ran = ['UNKNOWN' for x in range(3)]
        
    # placing rank and name into duty list
    # ensures that role and rank match
    i = 0
    check = []
    for j in range(3):
        if standby_list[i]['RANK_SORT'] in range(standby_list_ran_ref[j][0], standby_list_ran_ref[j][1]) and not standby_list[i]['NAME_IN_PS'] in check:
            standby_list_ran[j] = f'{standby_list[i]["RANK"]} {standby_list[i]["DISPLAY_NAME"]}'
            check.append(standby_list[i]['NAME_IN_PS'])
            i += 1 if i < len(standby_list) - 1 else 0

    return duty_list_ran, standby_list_ran

def obtain_adw(DATE):

    global everyone_list

    # obtain DAY from DATE
    date_datetime = datetime_convert(DATE)
    DAY = int(date_datetime.strftime('%#d'))

    # load in ADW sheet
    ADW_df = open_sheet(DATE, 'ADW')

    adw_list = []

    # obtains G1, G2 an G3A on that day and places them in a list
    for x in range(5, 8):
        adw_list.append(ADW_df.iloc[x, DAY + 1].upper().strip())

    return adw_list

def update_adw(DATE):

    global everyone_list

    # obtain DAY from DATE
    date_datetime = datetime_convert(DATE)
    DAY = int(date_datetime.strftime('%#d'))

    # load in callsign_ref as a dictionary
    with open('references/callsign_ref.json') as callsign_ref_json:
        callsign_ref_dict = load(callsign_ref_json)

    # load in ADW sheet
    ADW_df = open_sheet(DATE, 'ADW')

    def get_callsign(when):
        
        temp_list = []
        temp_list_split = []
        
        # places those on duty(A2(D) to G4) the previous day/on the day into a list
        for x in range(3, 10):
            temp_list.append(ADW_df.iloc[x, when].upper().strip())
        
        # splitting ones with multiple callsigns into seperate items
        for x in temp_list:
            if '/' in x:
                temp_list_split.extend(x.split('/'))
            else:
                temp_list_split.append(x)
        
        return temp_list_split
    
    # places those on duty the day before into a list and splits those with '/'
    adw_daybefore_list = get_callsign(DAY)
    
    # putting all those on duty the day before on changeover
    for x in adw_daybefore_list:
        callsign = re.sub('\(.*?\)?$', '', x)
        if callsign in callsign_ref_dict:
            update('NAME_IN_PS', callsign_ref_dict[callsign], 'STATUS_IN_PS', '\\')
    
    # places those on duty into a list and splits those with '/'
    adw_day_list = get_callsign(DAY + 1)

    # if (R) present, status is R
    # else status is HFD
    for x in adw_day_list:
        callsign = re.sub('\(.*?\)?$', '', x)
        if callsign in callsign_ref_dict:
            if '(R)' in x:
                update('NAME_IN_PS', callsign_ref_dict[callsign], 'STATUS_IN_PS', 'R')
            else:
                update('NAME_IN_PS', callsign_ref_dict[callsign], 'STATUS_IN_PS', 'HFD')

def categorise_ps():
    
    global everyone_list

    # load in definite_status json and indefinite_status as a dictionary
    with open('references/definite_status.json') as definite_status_json:
        definite_status_list = load(definite_status_json)
    
    with open('references/indefinite_status.json') as indefinite_status_json:
        indefinite_status_dict = load(indefinite_status_json)
    
    # these statuses take precedence over other statuses
    more_dominant_status = ['OFF', 'OSL', 'MA', 'MC', 'RSO', 'CCL', 'PCL', 'HL', 'UL', 'CL', 'FFI']

    for x in everyone_list:
        
        # check for statuses with SB and another status (not inclusive of U/S and O/S)
        # picks the other status
        if re.search('.{2,}/.{2,}', x['STATUS_IN_PS']) and 'SB' in x['STATUS_IN_PS']:
            x['DOMINANT_STATUS'] = [y for y in x['STATUS_IN_PS'].split('/') if y != 'SB'][0]
        
        # check for statuses with 2 different statuses (not inclusive of U/S, O/S and SB)
        # one is anything (not inclusive of SB) and the other is in the more dominant status list
        # picks the more dominant status
        elif re.search('.{2,}/.{2,}', x['STATUS_IN_PS']) and not set(more_dominant_status).isdisjoint(x['STATUS_IN_PS'].replace(' ', '').split('/')):
            x['DOMINANT_STATUS'] = [y for y in x['STATUS_IN_PS'].split('/') if y in more_dominant_status][0]
            
            # sets the display status as status in ps so that actual status can be seen on parade state
            x['DISPLAY_STATUS'] = x['STATUS_IN_PS']
        
        # if not in above conditions, dominant status = status in ps
        else:
            x['DOMINANT_STATUS'] = x['STATUS_IN_PS']
    
    # set everyone's display status to dominant status UNLESS display status is already known
    # category is unknown for ALL
    for x in everyone_list:
        if 'DISPLAY_STATUS' not in x:
            x['DISPLAY_STATUS'] = x['DOMINANT_STATUS']
        
        x['CATEGORY'] = 'UNKNOWN'

    # assigning category and display status to those common statuses
    for x in everyone_list:
        for y in definite_status_list:
            if x['DOMINANT_STATUS'] == y['DOMINANT_STATUS']:
                
                # if display status is unique, do not set display status as dominant status
                if x['DISPLAY_STATUS'] == x['DOMINANT_STATUS']:
                    x['DISPLAY_STATUS'] = y['DISPLAY_STATUS']
                
                x['CATEGORY'] = y['CATEGORY']
                break
    
    # for those with indefinite status (eg CSE, COURSE, CPC)
    # if these words are in status:
    # display status is dominant status
    # person will be placed in respective category
    for x in everyone_list:
        for category in indefinite_status_dict:
            if re.search('|'.join(indefinite_status_dict[category]), x['DOMINANT_STATUS']) and x['CATEGORY'] == 'UNKNOWN':
                x['DISPLAY_STATUS'] = x['DOMINANT_STATUS']
                x['CATEGORY'] = category
    
    # adding format for each person to be printed into parade state
    for x in everyone_list:
        
        print = []

        # if rank not present, do not add rank
        if x['RANK'] != 'NIL':
            print.append(x['RANK'])
        
        print.append(x['DISPLAY_NAME'])
        
        # if display status does not need to be displayed, do not add a display status
        if x['DISPLAY_STATUS'] != 'NIL':
            print.append(f'({x["DISPLAY_STATUS"]})')
        
        x['PRINT'] = ' '.join(print)
    
def front_ps(DATE, cos, flight):
    
    # function sorts personnel by category and flight and returns a sorted dictionary
    def sort_by_category_for_flight(flight):

        global everyone_list

        # making a dictionary to sort people with their respective category
        categorically_sorted = dict.fromkeys(['PRESENT', 'DYME', 'OFF', 'C/O', 'O/S', 'CSE', 'OSL', 'LL', 'MA', 'MC', 'RSO', 'CCL', 'PCL', 'HL', 'UL', 'CL', 'FFI', 'COPE TIGER', 'UNKNOWN'])

        # actual sorting WOWS !!!
        for x in categorically_sorted:
            categorically_sorted[x] = [y['PRINT'] for y in everyone_list if y['CATEGORY'] == x and y['FLIGHT'] == flight.upper()]
        
        return categorically_sorted
    
    # find the total strength of the given dictionary
    def total_strength(dict):
        
        y = 0
        
        for x in dict.values():
            y += len(x)
        
        return y
    
    # start of the printing
    cat = sort_by_category_for_flight(flight)
    
    known_ps = f'Good Day ALPHA, below is the Forecasted Parade State for {DATE}.\n\n' \
               f'COS: {cos}\n\n' \
               f'TOTAL STRENGTH ({total_strength(cat)})\n\n'
    
    # combines the string above with the different categories and their personnel into two strings (front_ps and unknown_ps) to be returned
    for x in cat:
            if x != 'UNKNOWN':
                known_ps += f'{x}: ({len(cat[x])})\n' + '\n'.join(cat[x]) + '\n\n'
            else:
                unknown_ps = '\n'.join(cat[x])

    return known_ps, unknown_ps
    
def middle_ps(DATE, bf_pax, lunch_pax, dinner_pax, flight):
    
    global everyone_list

    # <<< LUNCHERS ensures that NSF's are placed in the lunch first BEFORE REGULARS >>>
    
    # grabs the people that are present, from the flight stated and have a rank in the system
    lunchers = [x for x in everyone_list if x['CATEGORY'] == 'PRESENT' and x['FLIGHT'] == flight.upper()]

    # these people are sorted by NSF/REGULAR and then by rank
    # lowest rank/NSF -> highest rank/NSF -> lowest rank/REGULAR -> highest rank/REGULAR
    lunchers = sorted(lunchers, key=lambda x: (x.get('NOR'), x.get('RANK_SORT')))

    # take the first number=lunch_pax people and sort them by rank and then by NSF/REGULAR
    # reversed
    # <<< OUT OF THE number=lunch_pax >>>
    # highest rank/NSF -> highest rank/REGULAR -> lowest rank/REGULAR -> lowest rank/NSF
    lunchers = sorted(lunchers[:lunch_pax], key=lambda x: (x.get('RANK_SORT'), x.get('NOR')), reverse=True)

    # grab the rank + name for printing
    lunchers = [x['PRINT'] for x in lunchers]

    # makes seperate strings for bf and lunch, and dinner
    # for printing
    bf_and_lunch = f'[RATION SCANNERS]\n\n' \
                   f'BREAKFAST: [{bf_pax} PAX]\n' \
                   f'COS WILL SCAN ON BEHALF OF ALPHA\n\n' \
                   f'LUNCH: [{lunch_pax} PAX]\n' \
                   + '\n'.join(lunchers) + '\n\n'

    dinner = f'DINNER: [{dinner_pax} PAX]\n' \
             f'COS WILL SCAN ON BEHALF OF ALPHA\n\n' \

    # if it is a friday, do not print dinner
    if datetime_convert(DATE).weekday() != 4:
        return bf_and_lunch + dinner
    else:
        return bf_and_lunch

def end_ps(DATE):

    # obtain all informaton required to produce the end of the parade state
    duty_list, standby_list = load_standby_and_duty()
    adw_list = obtain_adw(DATE)

    # for printing
    return f'[DUTY CREW FOR {DATE}]\n' \
           f'OSC: {duty_list[0]}\n' \
           f'DYOSC: {duty_list[1]}\n' \
           f'ADSS: {duty_list[2]}\n' \
           f'ADSS: {duty_list[3]}\n' \
           f'ADWS: {duty_list[4]}\n' \
           f'ADWS: {duty_list[5]}\n\n' \
           f'[STANDBY CREW FOR {DATE}]\n' \
           f'AWO: {standby_list[0]}\n' \
           f'ADSS: {standby_list[1]}\n' \
           f'ADWS: {standby_list[2]}\n\n' \
           f'G1: {adw_list[0]}\n' \
           f'G2: {adw_list[1]}\n' \
           f'G3A: {adw_list[2]}'

def duty_compiler(cos, start_date, *args):
    
    # convert [DD][MM][YY] to datetime
    start_datetime = datetime_convert(start_date)

    # if end date provided, print from start to end date inclusive
    # if end date not provided, print weekend duty(SATURDAY and SUNDAY)
    if len(args) == 0:
        end_datetime = datetime_convert(start_date) + datetime.timedelta(days=1)
    else:
        end_datetime = datetime_convert(args[0])

    combine = ''

    # prints out all the days from start date to end date inclusive and returns a string
    while start_datetime <= end_datetime:
        load_ME_sheet(start_datetime.strftime('%d%m%y'))
        
        combine += end_ps(start_datetime.strftime('%d%m%y')) + '\n'
        combine += f'\nCOS: {cos}\n\n---------------------------------------------------\n'
        
        start_datetime += datetime.timedelta(days=1)

    return combine