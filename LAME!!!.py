import pandas as pd
import re
import telebot
import datetime
from json import load, dump

rank_list = {
    '3SG': 1,
    '2SG': 2,
    '1SG': 3,
    'SSG': 4,
    'MSG': 5,
    '3WO': 6,
    '2WO': 7,
    '1WO': 8,
    '2LT': 9,
    'LTA': 10,
    'CPT': 11
}

callsign_ref = {
    'IGNITE': 'OC',
    'SNAP': 'MARCUS',
    'TWO-FACE': 'MARC',
    'DO-IT': 'WEI KEONG',
    'CHISEL': 'MASON',
    'SPRITE': 'LAURA',
    'CLOUDY': 'JIA YING',
    'ZINC': 'JEN'
}

def update_status(person, status):
    for x in everyone:
        if x['NAME_IN_PS'] == person:
            x['STATUS'] = status
            break

def sort_by_rank(status):
    crew = {'KNOWN': [], 'UNKNOWN': []}

    # making of crew
    for x in everyone:
        if status == 'X':
            if status == x['STATUS']:
                try:
                    crew['KNOWN'].append({'DISPLAY_NAME': x['DISPLAY_NAME'], 'RANK_NUM': rank_list[x['RANK']], 'RANK': x['RANK']})
                except:
                    crew['UNKNOWN'].append(x['DISPLAY_NAME'])
        else:
            if status in x['STATUS']:
                try:
                    crew['KNOWN'].append({'DISPLAY_NAME': x['DISPLAY_NAME'], 'RANK_NUM': rank_list[x['RANK']], 'RANK': x['RANK']})
                except:
                    crew['UNKNOWN'].append(x['DISPLAY_NAME'])

    # sorting by rank in descending order
    crew['KNOWN'].sort(key=lambda x: x.get('RANK_NUM'), reverse=True)
    return crew

def update_flight_ps(flight):
    for x in flight:
        update_status(x['NAME_IN_PS'], x['STATUS'])

def rank_and_name(person_dict, category, check):
    if check == 'yes':
        try:
            category.append(person_dict['RANK'] + ' ' + person_dict['DISPLAY_NAME'] + ' ' + '(' + person_dict['STATUS'] + ')')
        except:
            category.append(person_dict['DISPLAY_NAME'] + ' ' + '(' + person_dict['STATUS'] + ')')
    elif check == 'no':
        try:
            category.append(person_dict['RANK'] + ' ' + person_dict['DISPLAY_NAME'])
        except:
            category.append(person_dict['DISPLAY_NAME'])

def sort(flight):
    for x in flight:
        if x['STATUS'] == '' or x['STATUS'] == 'SB' or 'ROUTE FAM' in x['STATUS']:
            rank_and_name(x, present, 'no')
        elif x['STATUS'] == 'X':
            rank_and_name(x, dyme, 'no')
        elif x['STATUS'] == 'OFF':
            rank_and_name(x, off, 'no')
        elif x['STATUS'] == '\\':
            rank_and_name(x, co, 'no')
        elif x['STATUS'] == 'SP' or x['STATUS'] == 'HFD' or x['STATUS'] == 'R' or x['STATUS'] == 'XVS' or x['STATUS'] == 'U/S' or x['STATUS'] == 'ESCORT' or x['STATUS'] == 'IMT' or x['STATUS'] == 'CS' or x['STATUS'] == 'ME' or 'AFTC' in x['STATUS'] or 'CPC' in x['STATUS']:
            rank_and_name(x, os, 'yes')
        elif 'CSE' in x['STATUS'] or x['STATUS'] == 'SIC' or x['STATUS'] == 'RIGGER' or x['STATUS'] == 'OEMP' or 'COURSE' in x['STATUS'] or x['STATUS'] == 'GWT':
            rank_and_name(x, cse, 'yes')
        elif x['STATUS'] == 'OSL':
            rank_and_name(x, osl, 'no')
        elif x['STATUS'] == 'LL':
            rank_and_name(x, ll, 'no')
        elif x['STATUS'] == 'MA':
            rank_and_name(x, ma, 'no')
        elif x['STATUS'] == 'MC':
            rank_and_name(x, mc, 'no')
        elif x['STATUS'] == 'RSO':
            rank_and_name(x, rso, 'no')
        elif x['STATUS'] == 'CCL':
            rank_and_name(x, ccl, 'no')
        elif x['STATUS'] == 'PCL':
            rank_and_name(x, pcl, 'no')
        elif x['STATUS'] == 'HL':
            rank_and_name(x, hl, 'no')
        elif x['STATUS'] == 'UL':
            rank_and_name(x, ul, 'no')
        elif x['STATUS'] == 'CL':
            rank_and_name(x, cl, 'no')
        elif x['STATUS'] == 'FFI':
            rank_and_name(x, ffi, 'no')
        elif '/' in x['STATUS']:
            if 'OFF' in x['STATUS'] and 'SB' in x['STATUS']:
                rank_and_name(x, off, 'no')
            elif 'OFF' in x['STATUS']:
                rank_and_name(x, off, 'yes')
            elif 'OSL' in x['STATUS']:
                rank_and_name(x, osl, 'yes')
            else:
                rank_and_name(x, unknown, 'yes')
        else:
            rank_and_name(x, unknown, 'yes')

def update_everyone(DATE):
    # declaring alpha, bravo and others as global variables
    global everyone
    global alpha
    global bravo
    global others

    # resetting
    everyone = []
    alpha = []
    bravo = []
    others = []

    # opening of each filght file and putting in respective lists
    with open('ALPHA.json') as ALPHA_json:
        alpha = load(ALPHA_json)

    with open('BRAVO.json') as BRAVO_json:
        bravo = load(BRAVO_json)

    with open('OTHERS.json') as OTHERS_json:
        others = load(OTHERS_json)

    # combining each flight's personnel into one list called everyone
    everyone.extend(alpha)
    everyone.extend(bravo)
    everyone.extend(others)

    # setting everyone's status to UNKNOWN
    for x in everyone:
        x['STATUS'] = 'U'

    # setting all those not in PS excel sheet to PRESENT
    for x in callsign_ref.values():
        update_status(x, '')

    # splitting [DD][MM][YY] removing trailing zeros and converting it into integers
    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')

    DAY = int(date_datetime.strftime('%#d'))
    MONTH_NUM = int(date_datetime.strftime('%#m'))
    YEAR = int(date_datetime.strftime('%#y'))

    # months_in_words = ["JAN", "FEB", "MAR", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPT", "OCT", "NOV", "DEC"]
    # MONTH = months_in_words[MONTH_NUM - 1]

    # # loading in of parade state and adw from google sheets
    # parade_state_url = f"https://docs.google.com/spreadsheets/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/gviz/tq?tqx=out:csv&sheet={MONTH}%2020{YEAR}"
    # adw_url = f"https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/gviz/tq?tqx=out:csv&sheet={MONTH}%20{YEAR}"

    parade_state_df = pd.read_csv('ME_2(23).csv', keep_default_na=False)
    adw_df = pd.read_csv('ADW_2(23).csv')

    # empty spots filled with 'UNKNOWN'
    adw_df = adw_df.fillna('UNKNOWN')

    # list to check if anyone's name is repeated again
    check = []

    # making a list for the actual parade state
    # NOTE: in FEB Senior Isaac is at row 60
    for x in range(9, len(parade_state_df) - 33):
        if x != 60:
            if parade_state_df.iloc[x, 0] != '':
                if parade_state_df.iloc[x, 0] not in check:
                    update_status(parade_state_df.iloc[x, 0].upper(), parade_state_df.iloc[x, DAY].upper())
                    check.append(parade_state_df.iloc[x, 0].upper())

    # temp variable for SB crew
    adw_daybefore = []

    # checking for adw the day before to see who is on standby
    for x in range(7):
        adw_daybefore.append(adw_df.iloc[3 + x, DAY].upper())

    adw_daybefore_split = []

    # removing /
    for x in adw_daybefore:
        if '/' in x:
            adw_daybefore_split.extend(re.split('/', x))
        else:
            adw_daybefore_split.append(x)

    # removing (R) and (HF)
    for x in adw_daybefore_split:
        if '(' in x:
            callsign = re.sub('\(.*?\)?$', '', x)
        else:
            callsign = x

        if callsign in callsign_ref:
            update_status(callsign_ref[callsign], '\\')

    global adw
    adw = []

    # checking for adw the day to see who is on duty
    for x in range(7):
        adw.append(adw_df.iloc[3 + x, DAY + 1].upper())

    adw_split = []

    # removing /
    for x in adw:
        if '/' in x:
            adw_split.extend(re.split('/', x))
        else:
            adw_split.append(x)

    # placing those (R), (HFD) or NONE with their respective statuses
    for x in adw_split:
        if '(' in x:
            location = re.findall('\(.*?\)?$', x)[0]
            callsign = re.sub('\(.*?\)?$', '', x)
            if callsign in callsign_ref:
                if 'R' in location:
                    update_status(callsign_ref[callsign], 'R')
                elif 'H' in location:
                    update_status(callsign_ref[callsign], 'HFD')
        else:
            if x in callsign_ref:
                update_status(callsign_ref[x], 'HFD')

    # making of duty crew and sorting by rank
    duty_crew = sort_by_rank('X')

    # declaring duty crew as a global variable
    global osc_duty
    global dyosc_duty
    global adss1_duty
    global adss2_duty
    global adws1_duty
    global adws2_duty
    global unknown_duty

    # setting all as UNKNOWN
    osc_duty = 'UNKNOWN'
    dyosc_duty = 'UNKNOWN'
    adss1_duty = 'UNKNOWN'
    adss2_duty = 'UNKNOWN'
    adws1_duty = 'UNKNOWN'
    adws2_duty = 'UNKNOWN'
    unknown_duty = ''

    # categorisation of personnel into duty roles
    # checking if their rank corresponds to their role
    count = 0
    for x in duty_crew['KNOWN']:
        successful = False
        while not successful:
            if x['RANK_NUM'] in range(9, 12) and count == 0:
                osc_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] >= 5 and count == 1:
                dyosc_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(2, 9) and count == 2:
                adss1_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(2, 9) and count == 3:
                adss2_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(1, 3) and count == 4:
                adws1_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(1, 3) and count == 5:
                adws2_duty = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif count == 6:
                break
            else:
                count += 1

    if len(duty_crew['UNKNOWN']) != 0:
        unknown_duty = '\n'.join(duty_crew['UNKNOWN'])

    # making of standby crew and sorting by rank
    standby_crew = sort_by_rank('SB')

    # declaring SB as global variable
    global awo_standby
    global adss_standby
    global adws_standby
    global unknown_standby

    # setting all to unknown
    awo_standby = 'UNKNOWN'
    adss_standby = 'UNKNOWN'
    adws_standby = 'UNKNOWN'
    unknown_standby = ''

    # categorisation of personnel into standby roles
    # checking if their rank corresponds to their role
    count = 0
    for x in standby_crew['KNOWN']:
        successful = False
        while not successful:
            if x['RANK_NUM'] in range(9, 12) and count == 0:
                awo_standby = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(2, 9) and count == 1:
                adss_standby = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif x['RANK_NUM'] in range(1, 3) and count == 2:
                adws_standby = x['RANK'] + ' ' + x['DISPLAY_NAME']
                count += 1
                successful = True
            elif count == 3:
                break
            else:
                count += 1

    if len(standby_crew['UNKNOWN']) != 0:
        unknown_standby = '\n'.join(standby_crew['UNKNOWN'])

    # override statuses
    override_status(DATE)

    # with open('output.json', 'w') as json_file:
    #     dump(everyone, json_file, indent=1)

def parade_state_maker(flight):
    # copy from everyone list to alpha and bravo lists
    update_flight_ps(alpha)
    update_flight_ps(bravo)

    global present
    global dyme
    global off
    global co
    global os
    global cse
    global osl
    global ll
    global ma
    global mc
    global rso
    global ccl
    global pcl
    global hl
    global ul
    global cl
    global ffi
    global unknown

    present = []
    dyme = []
    off = []
    co = []
    os = []
    cse = []
    osl = []
    ll = []
    ma = []
    mc = []
    rso = []
    ccl = []
    pcl = []
    hl = []
    ul = []
    cl = []
    ffi = []
    unknown = []

    # sorts each member into respective status list
    sort(flight)

def print_personnel(category):
    return '\n'.join(category)

def obtain_name(username):
    with open('username_ref.json') as username_ref_json:
        username_ref = load(username_ref_json)

    if username in username_ref:
        return username_ref[username]
    else:
        return ''

def print_parade_state():
    ps_main = f'TOTAL STRENGTH ({len(alpha)})\n\n' \
              f'PRESENT: ({len(present)})\n' \
              f'{print_personnel(present)}\n\n' \
              f'DYME: ({len(dyme)})\n' \
              f'{print_personnel(dyme)}\n\n' \
              f'OFF: ({len(off)})\n' \
              f'{print_personnel(off)}\n\n' \
              f'C/O: ({len(co)})\n' \
              f'{print_personnel(co)}\n\n' \
              f'O/S: ({len(os)})\n' \
              f'{print_personnel(os)}\n\n' \
              f'CSE: ({len(cse)})\n' \
              f'{print_personnel(cse)}\n\n' \
              f'OSL: ({len(osl)})\n' \
              f'{print_personnel(osl)}\n\n' \
              f'LL: ({len(ll)})\n' \
              f'{print_personnel(ll)}\n\n' \
              f'MA: ({len(ma)})\n' \
              f'{print_personnel(ma)}\n\n' \
              f'MC: ({len(mc)})\n' \
              f'{print_personnel(mc)}\n\n' \
              f'RSO: ({len(rso)})\n' \
              f'{print_personnel(rso)}\n\n' \
              f'CCL: ({len(ccl)})\n' \
              f'{print_personnel(ccl)}\n\n' \
              f'PCL: ({len(pcl)})\n' \
              f'{print_personnel(pcl)}\n\n' \
              f'HL: ({len(hl)})\n' \
              f'{print_personnel(hl)}\n\n' \
              f'UL: ({len(ul)})\n' \
              f'{print_personnel(ul)}\n\n' \
              f'CL: ({len(cl)})\n' \
              f'{print_personnel(cl)}\n\n' \
              f'FFI: ({len(ffi)})\n' \
              f'{print_personnel(ffi)}\n\n' \

    return ps_main

    # if flight == 'bravo':
    #     ps_main = f'TOTAL STRENGTH ({len(bravo)}):\n\n' \
    #               f'PRESENT ({len(present)})\n' \
    #               f'{print_personnel(present)}\n\n' \
    #               f'O/S ({len(os)})\n' \
    #               f'{print_personnel(os)}\n\n' \
    #               f'DY ({len(dyme)})\n' \
    #               f'{print_personnel(dyme)}\n\n' \
    #               f'C/O ({len(co)})\n' \
    #               f'{print_personnel(co)}\n\n' \
    #               f'OFF ({len(off)})\n' \
    #               f'{print_personnel(off)}\n\n' \
    #               f'LL: ({len(ll)})\n' \
    #               f'{print_personnel(ll)}\n\n' \
    #
    #     return ps_main

def print_ration(DATE):
    lunch_pax = 7
    lunch = []

    # take bottom ranking people and put in lunch list
    present.reverse()

    for x in range(lunch_pax):
        lunch.append(present[x])

    present.reverse()
    lunch.reverse()

    # getting the day of the week
    day = datetime.datetime.strptime(DATE, '%d%m%y').weekday()

    bf_and_lunch = f'[RATION SCANNERS]\n\n' \
                   f'BREAKFAST: [5 PAX]\n' \
                   f'COS WILL SCAN ON BEHALF OF ALPHA\n\n' \
                   f'LUNCH: [{lunch_pax} PAX]\n' \
                   f'{print_personnel(lunch)}\n\n' \

    dinner = f'DINNER: [5 PAX]\n' \
             f'COS WILL SCAN ON BEHALF OF ALPHA\n\n' \

    # monday = 0, ... friday = 6
    # if it is a friday, don't print dinner
    # if it is not a friday, print dinner
    if day == 4:
        ration = bf_and_lunch
    else:
        ration = bf_and_lunch + dinner

    return ration

def print_duty(DATE):
    duty = f'[DUTY CREW FOR {DATE}]\n' \
           f'OSC: {osc_duty}\n' \
           f'DYOSC: {dyosc_duty}\n' \
           f'ADSS: {adss1_duty}\n' \
           f'ADSS: {adss2_duty}\n' \
           f'ADWS: {adws1_duty}\n' \
           f'ADWS: {adws2_duty}\n\n' \
           f'[STANDBY CREW FOR {DATE}]\n' \
           f'AWO: {awo_standby}\n' \
           f'ADSS: {adss_standby}\n' \
           f'ADWS: {adws_standby}\n\n' \
           f'G1: {adw[2]}\n' \
           f'G2: {adw[3]}\n' \
           f'G3A: {adw[4]}' \

    return duty

def weekend_duty(START_DATE, END_DATE, name):
    start_datetime = datetime.datetime.strptime(START_DATE, '%d%m%y')
    end_datetime = datetime.datetime.strptime(END_DATE, '%d%m%y')
    difference = end_datetime - start_datetime

    combined = []

    for x in range(difference.days + 1):
        current_datetime = start_datetime + datetime.timedelta(days=x)
        current_date = current_datetime.strftime('%d%m%y')
        update_everyone(current_date)
        combined.append(print_duty(current_date))
        combined.append(f'\nCOS: {name}\n\n---------------------------------------------------')

    return '\n'.join(combined)

def print_unknowns():
    unknown_string = f'UNKNOWN IN PARADE STATE ({len(unknown)} PAX):\n' \
                     f'{print_personnel(unknown)}' \

    unknown_duty_string = f'UNKNOWN DUTY CREW:\n' \
                          f'{unknown_duty}' \

    unknown_standby_string = f'UNKNOWN STANDBY CREW:\n' \
                             f'{unknown_standby}'

    all_unknown_string = ''

    if len(unknown) != 0:
        all_unknown_string = all_unknown_string + '\n\n' + unknown_string
    elif len(unknown_duty) != 0:
        all_unknown_string = all_unknown_string + '\n\n' + unknown_duty_string
    elif len(unknown_standby) != 0:
        all_unknown_string = all_unknown_string + '\n\n' + unknown_standby_string

    return all_unknown_string

def override_status(DATE):
    with open('OVERRIDE.json') as OVERRIDE_json:
        override = load(OVERRIDE_json)

    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')

    for x in override:
        start_datetime = datetime.datetime.strptime(x['START_DATE'], '%d%m%y')
        end_datetime = datetime.datetime.strptime(x['END_DATE'], '%d%m%y')
        if (start_datetime <= date_datetime <= end_datetime):
            update_status(x['NAME_IN_PS'], x['STATUS'])

def override_status_add(NAME_IN_PS, STATUS, START_DATE, END_DATE):
    with open('OVERRIDE.json') as OVERRIDE_json:
        override = load(OVERRIDE_json)

    override.append({'NAME_IN_PS': NAME_IN_PS, 'STATUS': STATUS, 'START_DATE': START_DATE, 'END_DATE': END_DATE })

    with open("OVERRIDE.json", "w") as outfile:
        dump(override, outfile, indent=1)

def print_override_list():
    with open('OVERRIDE.json') as OVERRIDE_json:
        override = load(OVERRIDE_json)

    # remove outdated statuses more than 3 days due
    for x in override:
        if datetime.datetime.strptime(x['END_DATE'], '%d%m%y') + datetime.timedelta(days=3) < datetime.datetime.now():
            override.remove(x)

    with open("OVERRIDE.json", "w") as outfile:
        dump(override, outfile, indent=1)

    with open('ALPHA.json') as ALPHA_json:
        alpha = load(ALPHA_json)

    check = []
    override_organised = {}
    combined_override_list = ['OVERRIDE LIST\n']

    # group the statuses with the people
    # then label them with rank + name
    for x in override:
        for y in alpha:
            if x['NAME_IN_PS'] == y['NAME_IN_PS']:
                if x['NAME_IN_PS'] not in check:
                    try:
                        override_organised[y['RANK'] + ' ' + y['DISPLAY_NAME']] = [[x['STATUS'], x['START_DATE'], x['END_DATE']]]
                    except:
                        override_organised[y['DISPLAY_NAME']] = [[x['STATUS'], x['START_DATE'], x['END_DATE']]]

                    check.append(x['NAME_IN_PS'])
                else:
                    try:
                        override_organised[y['RANK'] + ' ' + y['DISPLAY_NAME']].append([x['STATUS'], x['START_DATE'], x['END_DATE']])
                    except:
                        override_organised[y['DISPLAY_NAME']].append([x['STATUS'], x['START_DATE'], x['END_DATE']])

    # combining each individual person + status together to be printed
    for x in override_organised:
        single_person_string = f'{x}:\n'
        for y in override_organised[x]:
            status = f'{y[1]} to {y[2]} ({y[0]})\n'
            single_person_string = single_person_string + status

        combined_override_list.append(single_person_string)

    return '\n'.join(combined_override_list)

bot_token = '6005706881:AAENa--bPIik5iuk1ap1dAAlXVkBzKs-fM8'
bot = telebot.TeleBot(token=bot_token, parse_mode=None)

temporary_override_dict = {
    'NAME_IN_PS': '',
    'STATUS': '',
    'START_DATE': '',
    'END_DATE': ''
}

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, '/help - to find more commands')

@bot.message_handler(commands=['help'])
def help_page(message):
    bot.send_message(message.chat.id, 'NOTE: [DATE] will be in [DD][MM][YY] format\n'
                                      '(eg 20th Jan 2023 will be written as 200123)\n')

    bot.send_message(message.chat.id, 'Stuff you can do with the bot:\n\n'
                                      'TERMS OF REFERENCE:\n'
                                      '/tor - gives you the places where the bot takes information from\n\n'
                                      'PARADE STATE / DUTY COMMANDS:\n'
                                      '/f [DATE] - generates the parade state for that date\n'
                                      '/we [DATE] - generates the duty crew for the weekend\n'
                                      '(DATE should be a Saturday)\n'
                                      '/duty [START DATE] [END DATE] - generates the duty crew from the start date to the end date inclusive\n'
                                      '(used for things such as consecutive public holidays)\n\n'
                                      'OVERRIDE STATUS COMMANDS:\n'
                                      '(for things like MC/COURSES for multiple days that is not registered by the bot)\n'
                                      '/ol - list of personnel that are overridden\n'
                                      '/oa - add personnel such that a certain status is reflected from the start date to end date inclusive\n'
                                      '/or - remove personnel status from override list')

@bot.message_handler(commands=['f'])
def parade_state(message):
    arg = message.text.split()[1:]

    try:
        DATE = str(arg[0])
    except:
        bot.send_message(message.chat.id, 'Please enter a valid date.')
        return 1

    # try:
    #     update_everyone(DATE)
    # except:
    #     bot.send_message(message.chat.id, 'Please enter a valid date.')
    #     return 2

    start = datetime.datetime.now()
    update_everyone(DATE)
    parade_state_maker(alpha)
    end = datetime.datetime.now()
    print(end-start)

    bot.send_message(message.chat.id, f'Good Day ALPHA, below is the Forecasted Parade State for {DATE}.\n\n'
                                      f'COS: {obtain_name(message.from_user.username)}\n\n'
                                      f'{print_parade_state()}'
                                      f'---------------------------------------------------\n\n'
                                      f'{print_ration(DATE)}'
                                      f'---------------------------------------------------\n\n'
                                      f'{print_duty(DATE)}')

    if len(unknown) != 0 or len(unknown_duty) != 0 or len(unknown_standby) != 0:
        bot.send_message(message.chat.id, print_unknowns())

@bot.message_handler(commands=['we'])
def weekend(message):
    arg = message.text.split()[1:]

    # check if date is even entered
    try:
        START_DATE = str(arg[0])
    except:
        return 1

    name = obtain_name(message.from_user.username)

    try:
        start_datetime = datetime.datetime.strptime(START_DATE, '%d%m%y')
        end_datetime = start_datetime + datetime.timedelta(days=1)
        END_DATE = end_datetime.strftime('%d%m%y')

        bot.send_message(message.chat.id, weekend_duty(START_DATE, END_DATE, name))
    except:
        bot.send_message(message.chat.id, 'Please enter a valid date.')
        return 2

@bot.message_handler(commands=['duty'])
def duty(message):
    arg = message.text.split()[1:]

    # check if 2 dates entered
    try:
        START_DATE = arg[0]
        END_DATE = arg[1]
    except:
        return 1

    name = obtain_name(message.from_user.username)

    try:
        bot.send_message(message.chat.id, weekend_duty(START_DATE, END_DATE, name))
    except:
        bot.send_message(message.chat.id, 'Please enter a valid date.')
        return 2

@bot.message_handler(commands=['tor'])
def terms_of_reference(message):
    bot.send_message(message.chat.id, 'FOR TO:\n'
                                      '**Check your OSN email**\n\n'
                                      'https://docs.google.com/spreadsheets/d/1whbTO1tvIa2FpMyVTVTJZWsRjWRIqVPzPAGY4BGfrSk/edit?usp=drivesdk')

    bot.send_message(message.chat.id, 'FOR G1, G2 and G3A:\n\n'
                                      'https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/edit')

    bot.send_message(message.chat.id, 'FOR literally everything else:\n\n'
                                      'https://docs.google.com/file/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/edit?usp=docslist_api')

@bot.message_handler(commands=['ol'])
def override_list(message):
    bot.send_message(message.chat.id, print_override_list())

@bot.message_handler(commands=['oa'])
def override_add(message):
    with open('ALPHA.json') as ALPHA_json:
        alpha = load(ALPHA_json)

    # creation of keyboard
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add('EXIT')
    for x in alpha:
        try:
            markup.add(x['RANK'] + ' ' + x['DISPLAY_NAME'])
        except:
            markup.add(x['DISPLAY_NAME'])

    person_in_ps = bot.send_message(message.chat.id, 'Select person', reply_markup=markup)
    bot.register_next_step_handler(person_in_ps, override_add_person_step)

def override_add_person_step(message):
    if message.text == 'EXIT':
        bot.send_message(message.chat.id, 'Exit ok', reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    with open('ALPHA.json') as ALPHA_json:
        alpha = load(ALPHA_json)

        # if input has no rank, take name as input
        # if input has rank, take name as input - rank
        if len(message.text.split()) >= 2:
            display_name = message.text[4:]
        else:
            display_name = message.text

    for x in alpha:
        temporary_override_dict['NAME_IN_PS'] = display_name

    # creation of keyboard
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add('EXIT', 'MC', 'OSL', 'OFF', 'LL', 'MA', 'RSO', 'CCL', 'PCL', 'HL', 'UL', 'CL', 'FFI')

    status = bot.send_message(message.chat.id, 'Select status\n(if not on list just type in chat)', reply_markup=markup)
    bot.register_next_step_handler(status, override_add_status_step)

def override_add_status_step(message):
    if message.text == 'EXIT':
        bot.send_message(message.chat.id, 'Exit ok', reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    temporary_override_dict['STATUS'] = message.text.upper()
    date = bot.send_message(message.chat.id, 'Enter date like this:\n[START DATE] [END DATE]', reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(date, override_add_dates_step)

def override_add_dates_step(message):
    if message.text.upper() == 'EXIT':
        bot.send_message(message.chat.id, 'Exit ok')
        return

    try:
        arg = message.text.split()
        start_date = arg[0]
        end_date = arg[1]

        if len(start_date) != 6 or len(end_date) != 6:
            msg = bot.reply_to(message, 'Date invalid\n(if you want to exit, type exit)')
            bot.register_next_step_handler(msg, override_add_dates_step)
            return

        temporary_override_dict['START_DATE'] = start_date
        temporary_override_dict['END_DATE'] = end_date

        override_status_add(temporary_override_dict['NAME_IN_PS'], temporary_override_dict['STATUS'], temporary_override_dict['START_DATE'], temporary_override_dict['END_DATE'])
        bot.send_message(message.chat.id, 'Successfully added! use /ol to see full override list.')

    except:
        msg = bot.reply_to(message, 'Date invalid\n(if you want to exit, type exit)')
        bot.register_next_step_handler(msg, override_add_dates_step)
        return

@bot.message_handler(commands=['or'])
def override_remove(message):
    bot.send_message(message.chat.id, 'Unimplemented')
    bot.send_photo(message.chat.id, 'https://i.pinimg.com/736x/d2/cd/df/d2cddf8adb6cec81ad29a0c718fbfb19.jpg')

@bot.message_handler(content_types=['text'])
def not_commands(message):
    if message.text.lower() == 'howard':
        bot.send_message(message.chat.id, 'slay')
        bot.send_message(message.chat.id, '\U0001F485')

bot.infinity_polling(timeout=10, long_polling_timeout = 5)