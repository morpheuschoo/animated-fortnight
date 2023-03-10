import pandas as pd
import os
import datetime
from ujson import load, dump
from pytz import timezone
from pee_maker import csv_to_dataframe

# ------------------------------------------------RUNS THE WHOLE SHOW!!!------------------------------------------------
async def run_pee_scheduler(context):

    download_adw_and_me()
    obtain_merged_cells()

def download_adw_and_me():
    
    # remove all files from the ME and ADW folder
    for file in os.scandir('online_sheets/ME'):
        os.remove(file)

    for file in os.scandir('online_sheets/ADW'):
        os.remove(file)

    # obtain the current month in numbers
    current_month = int(datetime.datetime.now(timezone('Asia/Singapore')).strftime('%#m'))

    # obtain current year in numbers
    current_year = int(datetime.datetime.now(timezone('Asia/Singapore')).strftime('%y'))

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

    status_dict['ONLINE SHEETS'] = datetime.datetime.now(timezone('Asia/Singapore')).strftime('%d/%m/%y at %#I:%M %p')

    with open('status.json', 'w') as status_json:
        dump(status_dict, status_json, indent=1)

def obtain_merged_cells():

    # obtains the latest ME sheet available which includes merged cells
    # why do i need to do this?
    # because google sheets SUCKS and nothing can read merged cells
    # i only found this garbage method to read merged cells and it can't even access other sheets, only the most recent one
    ME_df_with_merge = pd.read_html('https://docs.google.com/spreadsheets/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD', index_col=0)[0].fillna('NIL')

    month_alpha_ref = ["JAN", "FEB", "MAR", "APR", "MAY", "JUNE", "JULY", "AUGUST", "SEPT", "OCT", "NOV", "DEC"]

    # obtains month in alphabets of sheet
    month_alpha = ME_df_with_merge.iloc[7, 5].split('-')[1].upper()

    # convert month of sheet to numbers
    month_num = month_alpha_ref.index(month_alpha) + 1

    # if month of sheet is not current month, do not run (indicated that a new sheet has been created)
    # this prevents the program from overriding this month's merged cells
    if month_num == int(datetime.datetime.now(timezone('Asia/Singapore')).strftime('%#m')):

        # obtain year of sheet
        # if sheet is JANUARY while current date is DECEMBER, YEAR will be next year
        # else, year is current year
        if month_num == 1 and datetime.datetime.now(timezone('Asia/Singapore')).strftime('%#m') == 12:
            year = int(datetime.datetime.now(timezone('Asia/Singapore')).strftime('%#y')) + 1
        else:
            year = int(datetime.datetime.now(timezone('Asia/Singapore')).strftime('%#y'))

        # reindex columns for sheet with merged cells
        ME_df_with_merge.columns = pd.RangeIndex(ME_df_with_merge.columns.size)

        # remove unnecessary rows and columns for sheet with merged cells
        ME_df_with_merge = ME_df_with_merge[ME_df_with_merge[0] != 'NIL']
        ME_df_with_merge.drop(ME_df_with_merge.columns[[1]], axis=1, inplace=True)
        ME_df_with_merge.drop(ME_df_with_merge.columns[[x for x in range(ME_df_with_merge.shape[1] - 9, ME_df_with_merge.shape[1])]], axis=1, inplace=True)

        # obtains the ME sheet with no merged cells
        ME_df_without_merge = pd.read_csv(f"https://docs.google.com/spreadsheets/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/gviz/tq?tqx=out:csv&sheet={month_alpha}%2020{year}").fillna('NIL')

        # reindex columns for sheet with no merged cells
        ME_df_without_merge.columns = pd.RangeIndex(ME_df_without_merge.columns.size)

        # remove unnecessary rows for sheet with no merged cells
        ME_df_without_merge = ME_df_without_merge[ME_df_without_merge[0] != 'NIL']
        ME_df_without_merge.drop(ME_df_without_merge.columns[[x for x in range(ME_df_without_merge.shape[1] - 9, ME_df_without_merge.shape[1])]], axis=1, inplace=True)

        # adds an extra column at the end of both dataframes
        # this is to allow for the program to iterrate through the whole row in the while loop below
        ME_df_with_merge['TEMP'] = 'NIL'
        ME_df_without_merge['TEMP'] = 'NIL'

        merge_columns_list = []
        merged_cells_list = []

        # detecting for merged cells
        for row in range(ME_df_with_merge.shape[0]):
            for column in range(ME_df_with_merge.shape[1]):
                
                # detects first instance of discrepancy (2nd cell of merged block)
                if ME_df_with_merge.iloc[row, column].strip() != ME_df_without_merge.iloc[row, column].strip() and column not in merge_columns_list:
                    
                    # obtains the start of merged cell
                    merge_start_column = column - 1
                    
                    # obtains status of merged cell
                    status_in_ps = ME_df_with_merge.iloc[row, column - 1].strip().upper()

                    merge_end_column = column

                    # iterrates through merged cell
                    # starting from 2nd cell to last cell + 1
                    while(ME_df_with_merge.iloc[row, merge_end_column].strip() != ME_df_without_merge.iloc[row, merge_end_column].strip()):
                        merge_end_column += 1

                    # finds the end of the merged cell
                    merge_end_column -= 1

                    # obtain name in parade state of personnel
                    name_in_ps = ME_df_with_merge.iloc[row, 0].upper().strip()

                    # add relevant details to override list (for merged cells)
                    merged_cells_list.append({'NAME_IN_PS': name_in_ps, 'STATUS_IN_PS': status_in_ps, 'START_DATE': datetime.datetime(2000 + year, month_num, merge_start_column).strftime('%d%m%y'), 'END_DATE': datetime.datetime(2000 + year, month_num, merge_end_column).strftime('%d%m%y')})

                    # adds all the column numbers which the merged cell occupies
                    # ensures that 'if' portion does not run again for the 3rd, 4th, 5th, ... part of the same merged cell
                    merge_columns_list = [x for x in range(merge_start_column, merge_end_column + 1)]
                
                # resets the merge_columns_list
                # indicating that it has passed the merged cell and can find another merged cell again
                if len(merge_columns_list) != 0 and column == merge_columns_list[-1]:
                    merge_columns_list = []

        # adds all the merged cells data to a json file
        with open('override/merged_cells.json', 'w') as merged_cells_json:
            dump(merged_cells_list, merged_cells_json, indent=1)
        
        # updating status file with date and time which online sheets were updated
        with open('status.json') as status_json:
            status_dict = load(status_json)

        status_dict['MERGED CELLS'][0] = datetime.datetime.now(timezone('Asia/Singapore')).strftime('%d/%m/%y at %#I:%M %p')
        status_dict['MERGED CELLS'][1] = 'continue'

        with open('status.json', 'w') as status_json:
            dump(status_dict, status_json, indent=1)
    else:
        
        # indicating that the merged cells json has stopeed updating
        with open('status.json') as status_json:
            status_dict = load(status_json)

        status_dict['MERGED CELLS'][1] = 'stop'

        with open('status.json', 'w') as status_json:
            dump(status_dict, status_json, indent=1)


# add something to update override_ps (remove outdated statuses)