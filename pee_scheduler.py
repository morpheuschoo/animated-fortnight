import os
import datetime
from ujson import load, dump
from pytz import timezone
from pee_maker import csv_to_dataframe

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

    # updating status file with date and time which online sheets were updated
    with open('status.json') as status_json:
        status_dict = load(status_json)

    status_dict['online_sheets'] = datetime.datetime.now(timezone('Asia/Singapore')).strftime('Updated as of %d/%m/%y at %#I:%M %p')

    with open('status.json', 'w') as status_json:
        dump(status_dict, status_json, indent=1)

# add something to update override_ps (remove outdated statuses)