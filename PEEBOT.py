import pandas as pd
from ujson import load, dump
import datetime
import re
import os

# loads in ME/ADW google sheet and returns it as a dataframe
def csv_to_dataframe(month_num, year, thing):
    
    month_alpha_ref = ["JAN", "FEB", "MAR", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPT", "OCT", "NOV", "DEC"]

    # converts months in numbers to months in aphabets
    month_alpha = month_alpha_ref[month_num - 1]

    if thing == 'ME':
        return pd.read_csv(f"https://docs.google.com/spreadsheets/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/gviz/tq?tqx=out:csv&sheet={month_alpha}%2020{year}").fillna('NIL')
    
    elif thing == 'ADW':
        return pd.read_csv(f"https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/gviz/tq?tqx=out:csv&sheet={month_alpha}%20{year}").fillna('NIL')

def download_adw_and_me():
    
    # remove all files from the ME and ADW folder
    for file in os.scandir('online_sheets/ME'):
        os.remove(file)

    for file in os.scandir('online_sheets/ADW'):
        os.remove(file)

    # obtain the current month in numbers and alphabets
    current_month = int(datetime.date.today().strftime('%#m'))

    # obtain current year in numbers
    current_year = int(datetime.date.today().strftime('%y'))

    # function to add/remove months from date given
    # return in format like (1, 23)
    def timedelta_months(month, year, add):
        
        new_month = ((month - 1) + add) % 12 + 1
        new_year = year + ((month - 1) + add) // 12
        return new_month, new_year

    for x in range(-1, 2):
        month_num, year = timedelta_months(current_month, current_year, x)
        
        # downloads google sheets as csv from online and stores it in respective folders
        ME_df = csv_to_dataframe(month_num, year, 'ME')
        ME_df.to_csv(f'online_sheets/ME/ME_{month_num}({year}).csv', index=False)  

        ADW_df = csv_to_dataframe(month_num, year, 'ADW')
        ADW_df.to_csv(f'online_sheets/ADW/ADW_{month_num}({year}).csv', index=False)

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

# function to update everyone list
def update(main_column, condition, edit_column, value):
    
    global everyone_list
    
    for x in everyone_list:
        if x[main_column] == condition:
            x[edit_column] = value

# loads in ME sheet and assigns statuses to each person
# status taken from ME sheet
def load_ME_sheet(DATE):

    global everyone_list

    everyone_list = []

    # obtain DAY from DATE
    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')
    DAY = int(date_datetime.strftime('%#d'))

    # loading in all external files into code as a dictionary/list
    with open('flight_personnel/ALPHA.json') as alpha_json:
        alpha_list = load(alpha_json)

    with open('flight_personnel/BRAVO.json') as bravo_json:
        bravo_list = load(bravo_json)

    with open('flight_personnel/OTHERS.json') as others_json:
        others_list = load(others_json)

    with open('references/callsign_ref.json') as callsign_ref_json:
        callsign_ref_dict = load(callsign_ref_json)

    with open('references/rank_sorting.json') as rank_sorting_json:
        rank_sorting_dict = load(rank_sorting_json)
    
    # load in ME sheet
    ME_df = open_sheet(DATE, 'ME')

    # assigning flight to personnel
    def update_flight(flight_dict, flight):
        for x in flight_dict:
            x['FLIGHT'] = flight

    update_flight(alpha_list, 'ALPHA')
    update_flight(bravo_list, 'BRAVO')
    update_flight(others_list, 'OTHERS')

    # merging alpha, bravo and others into one list called everyone
    everyone_list.extend(alpha_list + bravo_list + others_list)

    # assign UNKNOWN status to everyone
    for x in everyone_list:
        x['STATUS_IN_PS'] = 'UNKNOWN'

    # assign present(NIL) status to those not in ME_df (eg OC, ...)
    for x in callsign_ref_dict.values():
        update('NAME_IN_PS', x, 'STATUS_IN_PS', 'NIL')
    
    # assign status to personnel
    # status taken from ME sheet
    # leading and trailing whitespaces removed from name and status
    for x in range(9, len(ME_df) - 33):
        if ME_df.iloc[x, 0] != 'NIL' and x != 60:
            update('NAME_IN_PS', ME_df.iloc[x, 0].upper().strip(), 'STATUS_IN_PS', ME_df.iloc[x, DAY].upper().strip())
    
    # assign everyone a number to their rank for easy sorting
    for x in rank_sorting_dict:
        update('RANK', x, 'RANK_SORT', rank_sorting_dict[x])

def load_standby_and_duty():

    global everyone_list

    def sort_by_rank(temp_list):

        # remove personnel from list who do not have a rank
        for x in temp_list:
            if x['RANK_SORT'] == 'NIL':
                temp_list.remove(x)

        # sort list by rank
        # highest rank at the front, lowest rank at the back
        temp_list.sort(key=lambda x: x.get('RANK_SORT'), reverse=True)
    
        return temp_list
    
    # declare a duty list that contains the rank and name of personnel
    duty_list_ran = []
    
    # sort personnel on duty by rank
    duty_list = sort_by_rank([x for x in everyone_list if x['STATUS_IN_PS'] == 'X'])

    # placing rank and name into duty list
    # ensures that role and rank match
    count = 0
    for x in duty_list:
        successful = False
        while not successful:
            if x['RANK_SORT'] in range(9, 12) and count == 0:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] >= 5 and count == 1:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(2, 9) and count == 2:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(2, 9) and count == 3:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(1, 3) and count == 4:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(1, 3) and count == 5:
                duty_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif count == 6:
                break
            else:
                duty_list_ran.append('UNKNOWN')
                count += 1
    
    # declare a duty list that contains the rank and name of personnel
    standby_list_ran = []

    # sort personnel on standby by rank
    standby_list = sort_by_rank([x for x in everyone_list if 'SB' in x['STATUS_IN_PS']])
        
    # placing rank and name into standby list
    # ensures that role and rank match
    count = 0
    for x in standby_list:
        successful = False
        while not successful:
            if x['RANK_SORT'] in range(9, 12) and count == 0:
                standby_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(2, 9) and count == 1:
                standby_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif x['RANK_SORT'] in range(1, 3) and count == 2:
                standby_list_ran.append(x['RANK'] + ' ' + x['DISPLAY_NAME'])
                count += 1
                successful = True
            elif count == 3:
                break
            else:
                standby_list_ran.append('UNKNOWN')
                count += 1

    return duty_list_ran, standby_list_ran

def obtain_adw(DATE):

    global everyone_list

    # obtain DAY from DATE
    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')
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
    date_datetime = datetime.datetime.strptime(DATE, '%d%m%y')
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
        # removes whitespace before and after status
        if re.search('.{2,}/.{2,}', x['STATUS_IN_PS']) and 'SB' in x['STATUS_IN_PS']:
            x['DOMINANT_STATUS'] = [y.strip() for y in x['STATUS_IN_PS'].split('/') if y.strip() != 'SB'][0]
        
        # check for statuses with 2 different statuses (not inclusive of U/S, O/S and SB)
        # one is anything (not inclusive of SB) and the other is in the more dominant status list
        # picks the more dominant status
        # removes whitespace before and after status
        elif re.search('.{2,}/.{2,}', x['STATUS_IN_PS']) and not set(more_dominant_status).isdisjoint(x['STATUS_IN_PS'].replace(' ', '').split('/')):
            x['DOMINANT_STATUS'] = [y.strip() for y in x['STATUS_IN_PS'].split('/') if y.strip() in more_dominant_status][0]
            
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
        
        # if display status does not need t be displayed, do not add a display status
        if x['DISPLAY_STATUS'] != 'NIL':
            print.append('(' + x['DISPLAY_STATUS'] + ')')
        
        x['PRINT'] = ' '.join(print)
    
def front_ps(DATE, cos, flight):
    
    # function sorts personnel by category and flight and returns a sorted dictionary
    def sort_by_category_for_flight(flight):

        global everyone_list

        # making a dictionary to sort people with their respective category
        categorically_sorted = dict.fromkeys(['PRESENT', 'DYME', 'OFF', 'C/O', 'O/S', 'CSE', 'OSL', 'LL', 'MA', 'MC', 'RSO', 'CCL', 'PCL', 'HL', 'UL', 'CL', 'FFI', 'UNKNOWN'])

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
    
    front_ps = f'Good Day ALPHA, below is the Forecasted Parade State for {DATE}.\n\n' \
               f'COS: {cos}\n\n' \
               f'TOTAL STRENGTH ({total_strength(cat)})\n\n'

    # combines the string above with the different categories and their personnel into one string (front_ps) to be returned
    for x in cat:

            if x != 'UNKNOWN':
                front_ps += f'{x}: ({len(cat[x])})\n' + '\n'.join(cat[x]) + '\n\n'

    return front_ps
    

def middle_ps(DATE, bf_pax, lunch_pax, dinner_pax, flight):
    
    global everyone_list

    # <<< LUNCHERS ensures that NSF's are placed in the lunch first BEFORE REGULARS >>>
    
    # grabs the people that are present, from the flight stated and have a rank in the system
    lunchers = [x for x in everyone_list if x['CATEGORY'] == 'PRESENT' and x['FLIGHT'] == flight.upper() and x['RANK_SORT'] != 'NIL']

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
    if datetime.datetime.strptime(DATE, '%d%m%y').weekday() != 4:
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

def duty_compiler(username, start_date, *args):

    # open username_ref as a dict
    # username_ref matches the user's username to their rank + name printed in the parade state
    with open('references/username_ref.json') as username_ref_json:
        username_ref_dict = load(username_ref_json)
    
    # convert [DD][MM][YY] to datetime
    start_datetime = datetime.datetime.strptime(start_date, '%d%m%y')

    # if end date provided, print from start to end date inclusive
    # if end date not provided, print weekend duty(SATURDAY and SUNDAY)
    if len(args) == 0:
        end_datetime = datetime.datetime.strptime(start_date, '%d%m%y') + datetime.timedelta(days=1)
    else:
        end_datetime = datetime.datetime.strptime(args[0], '%d%m%y')

    combine = ''

    # prints out all the days from start date to end date inclusive and returns a string
    while start_datetime <= end_datetime:
        load_ME_sheet(start_datetime.strftime('%d%m%y'))
        
        combine += end_ps(start_datetime.strftime('%d%m%y')) + '\n'
        combine += f'\nCOS: {username_ref_dict[username]}\n\n---------------------------------------------------\n'
        
        start_datetime += datetime.timedelta(days=1)

    return combine

import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
# from dotenv import load_dotenv

# tells you when the programme starts / stops (in console)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="/help - tells you what the bot can do")

# /f [DATE]
async def print_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # try:
    DATE = context.args[0]

    if len(DATE) != 6:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Date should be 6 numbers long -_-')
        return
    
    # open username_ref as a dict
    # username_ref matches the user's username to their rank + name printed in the parade state
    with open('references/username_ref.json') as username_ref_json:
        username_ref_dict = load(username_ref_json)

    # load in all the stuff required to print parade state
    load_ME_sheet(DATE)
    update_adw(DATE)
    categorise_ps()

    # sends the message
    await context.bot.send_message(chat_id=update.effective_chat.id, text = f'{front_ps(DATE, username_ref_dict[update.message.from_user.username], "alpha")}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{middle_ps(DATE, 5, 7, 5, "alpha")}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{end_ps(DATE)}')
    
    # except:
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in a valid date (uh oh)')
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
    #     return

# /we [DATE]
async def print_weekend_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        DATE = context.args[0]

        if len(DATE) != 6:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Date should be 6 numbers long -_-')
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{duty_compiler(update.message.from_user.username, DATE)}')
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in a valid date (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return

# /duty [START DATE] [END DATE]
async def print_multiple_weekend_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_date = context.args[0]
        end_date = context.args[1]
        
        if len(start_date) != 6 or len(end_date) != 6:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Date should be 6 numbers long -_-')
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{duty_compiler(update.message.from_user.username, start_date, end_date)}')
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in valid dates (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return

if __name__ == '__main__':
    
    # load_dotenv()

    # API_KEY = os.getenv('API_KEY')

    bot = ApplicationBuilder().token('6005706881:AAENa--bPIik5iuk1ap1dAAlXVkBzKs-fM8').build()

    # /start
    bot.add_handler(CommandHandler('start', start))

    # /f [DATE]
    bot.add_handler(CommandHandler('f', print_ps))

    # /we [DATE]
    bot.add_handler(CommandHandler('we', print_weekend_duty))

    # /duty [START DATE] [END DATE]
    bot.add_handler(CommandHandler('duty', print_multiple_weekend_duty))
    
    bot.run_polling()
