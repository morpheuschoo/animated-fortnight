import numpy as np
import pandas as pd
from ujson import load, dump

def convert_flight_personnel_to_excel():
    
    # load in all external files as a list
    with open('flight_personnel/ALPHA.json') as alpha_json:
        alpha_list = load(alpha_json)

    with open('flight_personnel/BRAVO.json') as bravo_json:
        bravo_list = load(bravo_json)

    with open('flight_personnel/OTHERS.json') as others_json:
        others_list = load(others_json)

    # convert all files to a dataframe
    alpha_df = pd.DataFrame(alpha_list)
    bravo_df = pd.DataFrame(bravo_list)
    others_df = pd.DataFrame(others_list)

    # combining all flight's dataframe together
    # adds a blank column between them
    alpha_df[np.NaN] = np.NaN
    bravo_df[np.NaN] = np.NaN

    everyone_df = pd.merge(alpha_df, bravo_df, left_index=True, right_index=True, how='outer')
    everyone_df = pd.merge(everyone_df, others_df, left_index=True, right_index=True, how='outer')

    # renaming column header
    everyone_df.columns = [
        'RANK', 'DSIPLAY_NAME', 'NAME_IN_PS', 'NOR', np.NaN,
        'RANK', 'DSIPLAY_NAME', 'NAME_IN_PS', 'NOR', np.NaN,
        'RANK', 'DSIPLAY_NAME', 'NAME_IN_PS', 'NOR'
    ]

    # converting dataframe into an excel file to be sent
    # formatting excel file for better viewing
    writer = pd.ExcelWriter('files_on_the_move/to_be_sent/flight_personnel.xlsx')
    everyone_df.to_excel(writer, sheet_name='main', index=False)

    # <<< set column width >>>
    # key: index of column
    # value: width of column
    column_width_ref = {0:6, 1:20, 2:20, 3:10, 4:1, 5:6, 6:20, 7:20, 8:10, 9:1, 10:6, 11:20, 12:20, 13:10, 14:1}

    for x in column_width_ref:
        writer.sheets['main'].set_column(x, x, column_width_ref[x])

    writer.close()

def edit_flight_personnel_files():

        # loading in external files into code as a dictionary
    with open('references/rank_sorting.json') as rank_sorting_json:
        rank_sorting_dict = load(rank_sorting_json)

    # loading in personnel file sent by user as a dataframe
    flight_personnel_df = pd.read_excel('files_on_the_move/to_be_received/flight_personnel.xlsx').fillna('NIL')

    flight_personnel_dict = {'ALPHA': [], 'BRAVO': [], 'OTHERS': []}

    flight_personnel_dict_ref = {'ALPHA': [0, 1, 2, 3], 'BRAVO': [5, 6, 7, 8], 'OTHERS': [10, 11, 12, 13]}

    # iterrates through list
    # creates new list based on what was in excel file
    # ignores those rows where NAME_IN_PS is NIL
    # (indicates nobody is in that row)
    for row in range(flight_personnel_df.shape[0]):
        for flight in flight_personnel_dict_ref:
            
            if flight_personnel_df.iloc[row, flight_personnel_dict_ref[flight][2]] != 'NIL':
                flight_personnel_dict[flight].append(
                    {
                    'RANK': flight_personnel_df.iloc[row, flight_personnel_dict_ref[flight][0]],
                    'DISPLAY_NAME': flight_personnel_df.iloc[row, flight_personnel_dict_ref[flight][1]],
                    'NAME_IN_PS': flight_personnel_df.iloc[row, flight_personnel_dict_ref[flight][2]],
                    'NOR': flight_personnel_df.iloc[row, flight_personnel_dict_ref[flight][3]]
                    }
                )

    # assign everyone a number to their rank for easy sorting
    for flight in flight_personnel_dict:
        for personnel in flight_personnel_dict[flight]:
            personnel['RANK_SORT'] = rank_sorting_dict[personnel['RANK']]

    # sort everyone in their individual flights by RANK FIRST then NSF/REGULAR
    # highest rank -> lowest rank
    # regulars in front of NSF's
    for flight in flight_personnel_dict:
        flight_personnel_dict[flight] = sorted(flight_personnel_dict[flight], key=lambda x: (x.get('RANK_SORT'), x.get('NOR')), reverse=True)

    # removes RANK_SORT from everyone
    for flight in flight_personnel_dict:
        for personnel in flight_personnel_dict[flight]:
            del personnel['RANK_SORT']

    # overrides personnel file with newly changed ones
    with open('flight_personnel/ALPHA.json', 'w') as alpha_json:
        dump(flight_personnel_dict['ALPHA'], alpha_json, indent=1)

    with open('flight_personnel/BRAVO.json', 'w') as bravo_json:
        dump(flight_personnel_dict['BRAVO'], bravo_json, indent=1)

    with open('flight_personnel/OTHERS.json', 'w') as others_json:
        dump(flight_personnel_dict['OTHERS'], others_json, indent=1)