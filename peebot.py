import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler
from pee_maker import *
from pee_scheduler import run_pee_scheduler
from pee_editor import convert_flight_personnel_to_excel, edit_flight_personnel_files
import os
from ujson import dump
from pytz import timezone
from dotenv import load_dotenv

# tells you when the programme starts / stops (in console)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ------------------------------------------------/START------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="/help - tells you what the bot can do")

# ------------------------------------------------/HELP------------------------------------------------
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='NOTE: [DATE] will be in [DD][MM][YY] format\n'
                                                                          '(eg 20th Jan 2023 will be written as 200123)\n')

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='TERMS OF REFERENCE:\n'
                                        '/tor - gives you the places where the bot takes information from\n\n'
                                        'PARADE STATE / DUTY COMMANDS:\n'
                                        '/f [DATE] - generates the parade state\n'
                                        '/we [DATE] - generates the duty crew\n'
                                        '(DATE should be a Saturday)\n'
                                        '/duty [START DATE] [END DATE] - generates the duty crew from the start date to the end date inclusive\n\n'
                                        'OVERRIDE STATUS COMMANDS:\n'
                                        '(for things like MC)\n'
                                        '/ol - shows override list\n'
                                        '/oa - add to override list\n'
                                        '/or - remove from override list\n\n'
                                        'EDIT PERSONNEL:\n'
                                        '/obtainfiles - obtain personnel file\n'
                                        '/ep - edit personnel file\n\n'
                                        'ADMIN COMMANDS:\n'
                                        '/status - shows when was data last updated\n'
                                        '/update - updates the database\n')

# ------------------------------------------------/TOR------------------------------------------------
async def tor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='\<\<\< TERMS OF REFERENCE \>\>\>\n\n'
                                        'FOR TO: '
                                        'CHECK OSN EMAIL\n'
                                        'FOR CSS: '
                                        '[LINK](https://docs.google.com/spreadsheets/d/1whbTO1tvIa2FpMyVTVTJZWsRjWRIqVPzPAGY4BGfrSk/edit?usp=drivesdk)\n'
                                        'FOR WEAPON CONTROLLERS: '
                                        '[LINK](https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/edit)\n'
                                        'FOR ME SHEETS: '
                                        '[LINK](https://docs.google.com/file/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/edit?usp=docslist_api)\n',
                                        parse_mode='MarkdownV2', disable_web_page_preview=True)

# ------------------------------------------------MAKES THE STRING TO BE USED IN /STATUS and /UPDATE------------------------------------------------
def print_status_string():
    with open('status.json') as status_json:
        status_dict = load(status_json)
    
    status_string = '<<< STATUSES >>>\n\n'

    # combine all statuses into one string to be reutrned
    status_string += f'ONLINE SHEETS:\nUPDATED AS OF {status_dict["ONLINE SHEETS"]}\n\n'
    
    status_string += f'MERGED CELLS:\n'

    if status_dict['MERGED CELLS'][1] == 'continue':
        status_string += f'UPDATED AS OF {status_dict["MERGED CELLS"][0]}\n\n'
    else:
        status_string += f'STOPPED UPDATING AS OF {status_dict["MERGED CELLS"][0]}\n\n' 
    
    return status_string

# ------------------------------------------------/STATUS------------------------------------------------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=print_status_string())

# ------------------------------------------------/UPDATE------------------------------------------------
async def update_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Updating...')

    await run_pee_scheduler(context)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=print_status_string())

# ------------------------------------------------/OBTAINFILES------------------------------------------------
async def obtain_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # makes the file to be sent
    convert_flight_personnel_to_excel()

    await context.bot.send_document(update.effective_chat.id,
                                    open(f'files_on_the_move/to_be_sent/flight_personnel.xlsx', 'rb'))

# ------------------------------------------------TEMP PROCESSESS USERNAME------------------------------------------------
def username_processor(chat_id, username):
    
    # open username_ref as a list
    with open('references/username_ref.json') as username_ref_json:
        username_ref_list = load(username_ref_json)

    for x in username_ref_list:
        if username == x['username'] or chat_id == x['chat_id']:
            x['chat_id'] = chat_id
            cos = x['cos']
    
    if not username in [x['username'] for x in username_ref_list] and not chat_id in [x['chat_id'] for x in username_ref_list]:
        username_ref_list.append({'username': username, 'chat_id': chat_id, 'cos': ''})
        
        cos = ''
    
    with open('references/username_ref.json', 'w') as username_ref_json:
            dump(username_ref_list, username_ref_json, indent=1)
    
    return cos

# ------------------------------------------------/f [DATE]------------------------------------------------
async def print_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        
        # if no date inputted, next day parade state is generated
        # in Singapore timezone
        if len(context.args) != 1:
            DATE = (datetime.datetime.now(timezone('Asia/Singapore')) + datetime.timedelta(days=1)).strftime('%d%m%y')
        else:
            DATE = context.args[0]

        # ensures that date is numeric and is 6 numbers long
        if not re.search('[0-9]{6}', DATE):
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Date should be 6 numbers long -_-')
            return

        # load in all the stuff required to print parade state
        load_ME_sheet(DATE)
        update_adw(DATE)
        load_override_lists(DATE)
        categorise_ps()

        known_ps, unknown_ps = front_ps(DATE, username_processor(update.effective_chat.id, update.message.from_user.username), "alpha")

        # sends the parade state
        await context.bot.send_message(chat_id=update.effective_chat.id, text = f'{known_ps}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{middle_ps(DATE, 5, 6, 5, "alpha")}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{end_ps(DATE)}')

        # if there are unknowns in parade state, unknowns will be listed and sent in another message
        if unknown_ps != "":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'UNKNOWN:\n{unknown_ps}')
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in a valid date (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return

# ------------------------------------------------/WE [DATE]------------------------------------------------
async def print_weekend_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        
        # if no date inputted, next day + next next day duty crew is generated
        # in Singapore timezone
        if len(context.args) != 1:
            DATE = (datetime.datetime.now(timezone('Asia/Singapore')) + datetime.timedelta(days=1)).strftime('%d%m%y')
        else:
            DATE = context.args[0]

        # ensures that date is numeric and is 6 numbers long
        if not re.search('[0-9]{6}', DATE):
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Date should be 6 numbers long -_-')
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=duty_compiler(username_processor(update.effective_chat.id, update.message.from_user.username), DATE))
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in a valid date (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return

# ------------------------------------------------/DUTY [START DATE] [END DATE]------------------------------------------------
async def print_multiple_weekend_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_date = context.args[0]
        end_date = context.args[1]
        
        # ensures that both dates are numeric and are 6 numbers long
        if not re.search('[0-9]{6}', start_date) or not re.search('[0-9]{6}', end_date):
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Dates should be 6 numbers long -_-')
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=duty_compiler(username_processor(update.effective_chat.id, update.message.from_user.username), start_date, end_date))
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in valid dates (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return
    
# ------------------------------------------------/OL------------------------------------------------
async def print_override_ps_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('override/merged_cells.json') as merged_cells_json:
        merged_cells_list = load(merged_cells_json)

    with open('override/override_ps.json') as override_ps_json:
        override_ps_list = load(override_ps_json)
    
    with open('status.json') as status_json:
        status_dict = load(status_json)
    
    everyone_list = load_163()

    # formats statuses together with rank + display name for printing
    def print_combined_list(list_in_question):
        combined = {}
        print_combined = ''

        # iterrates through the override ps list
        # creates a dictionary:
        # KEY: name in parade state
        # VALUE: [0]-rank + displayed name / [1 and above]-status with start date and end date
        for x in list_in_question:
            for y in everyone_list:
                if x['NAME_IN_PS'] == y['NAME_IN_PS']:
                    if x['NAME_IN_PS'] not in combined:
                        combined[x['NAME_IN_PS']] = [y['RANK'] + ' ' + y['DISPLAY_NAME'] if y['RANK'] != 'NIL' else y['DISPLAY_NAME']]
                    
                    combined[x['NAME_IN_PS']].append(f'{x["START_DATE"]} to {x["END_DATE"]} ({x["STATUS_IN_PS"]})')

        for x in combined.values():
            print_combined += f'{x[0]}:\n' + '\n'.join(x[1:]) + '\n\n'

        return print_combined
    
    print_merged_cells_combined =  '<<< MERGED CELLS >>>\n'

    if status_dict['MERGED CELLS'][1] == 'continue':
        print_merged_cells_combined += f'UPDATED AS OF {status_dict["MERGED CELLS"][0]}\n\n'
    else:
        print_merged_cells_combined += f'STOPPED UPDATING AS OF {status_dict["MERGED CELLS"][0]}\n\n'
    
    print_merged_cells_combined += print_combined_list(merged_cells_list)

    print_override_ps_combined = '<<< OVERRIDE LIST >>>\n\n' + print_combined_list(override_ps_list)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=print_merged_cells_combined)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=print_override_ps_combined)

# ------------------------------------------------/OA------------------------------------------------
temp_override_ps_dict = dict.fromkeys(['NAME_IN_PS', 'STATUS_IN_PS', 'START_DATE', 'END_DATE'])

# /oa [1st] - asks for NAME
async def override_ps_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    
    # load in ALPHA flight as a list
    with open('flight_personnel/ALPHA.json') as alpha_json:
        alpha_list = load(alpha_json)
    
    keyboard = []
        
    # make the keyboard such that one row has only one name
    # format: [[NAME(1)], [NAME(2)], [NAME(3)], ...]
    for x in alpha_list:
        keyboard.append([x['RANK'] + ' ' + x['DISPLAY_NAME'] if x['RANK'] != 'NIL' else x['DISPLAY_NAME']])

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Select a personnel\n'
                                        '/exit to exit',
                                   reply_markup=ReplyKeyboardMarkup(keyboard, input_field_placeholder='Personnel'))

    return 1

# /oa [2nd] - saves NAME and asks for STATUS
async def override_ps_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    everyone_list = load_163()
    
    # obtains the display name from reply
    DISPLAY_NAME = update.message.text if len(update.message.text.split()) == 1 else update.message.text[4:]

    # obtains and saves the name in parade state of the respective personnel
    for x in everyone_list:
        if x['DISPLAY_NAME'] == DISPLAY_NAME:
            temp_override_ps_dict['NAME_IN_PS'] = x['NAME_IN_PS']
            break

    keyboard = [['MC', 'OSL', 'OFF'], ['LL', 'MA', 'RSO'], ['CCL', 'PCL', 'HL'], ['UL', 'CL', 'FFI']]

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text='Select a status\n'
                                        'For custom statuses, type using the keyboard\n'
                                        '/exit to exit', 
                                   reply_markup=ReplyKeyboardMarkup(keyboard, input_field_placeholder='Status'))

    return 2

# /oa [3rd] - saves STATUS and asks for START DATE to END DATE
async def override_ps_add_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # saves the status, clearing up any input error
    # (eg. trailing, leading whitespaces or whitespaces beside '/')
    temp_override_ps_dict['STATUS_IN_PS'] = re.sub('\s*/\s*', '/', update.message.text.upper().strip())
    
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text='Input: [START DATE] [END DATE]\n'
                                        '/exit to exit',
                                   reply_markup=ReplyKeyboardRemove())
    
    return 3

# /oa [4th] - saves START DATE to END DATE
async def override_ps_add_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
    
        # ensures that there are 2 dates, both dates are numeric and are 6 numbers long
        if not re.search('[0-9]{6} [0-9]{6}', update.message.text):
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Dates invalid\n'
                                                '/exit to exit')
            return 3
        
        # saves start and end date
        start_date = update.message.text.split()[0]
        end_date = update.message.text.split()[1]
        
        # ensures that the start date is before the end date
        if datetime_convert(start_date) > datetime_convert(end_date):
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Start date > End date\n'
                                                'bruh moment')
            return 3
        
        temp_override_ps_dict['START_DATE'], temp_override_ps_dict['END_DATE'] = start_date, end_date

        # adds the user inputted details into the override_ps file
        with open('override/override_ps.json') as override_ps_json:
            override_ps_list = load(override_ps_json)
        
        override_ps_list.append(temp_override_ps_dict)

        with open('override/override_ps.json', 'w') as override_ps_json:
            dump(override_ps_list, override_ps_json, indent=1)

        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text='Status added successfully! Use /ol to view full override list')

        return ConversationHandler.END
    
    # this except catches dates that are not valid dates
    # (eg 100000)
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Dates invalid\n'
                                            '/exit to exit')
        
        return 3

# ------------------------------------------------/EP------------------------------------------------
# /ep [1st] - sends FLIGHT_PERSONNEL FILE and INSTRUCTIONS
async def edit_personnel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await obtain_files(update, context)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='\<\<\< INSTRUCTIONS \>\>\>\n\n'
             'HEADER:\n'
             'RANK \- rank of personnel\n'
             'DISPLAY\_NAME \- name displayed in PS msg\n'
             'NAME\_IN\_PS \- name displayed in [ME\_df](https://docs.google.com/file/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/edit?usp=docslist_api)\n'
             'NOR \- NSF or REGULAR\n\n'
             'COLUMN REPRESENTATION:\n'
             'COLUMN 1 \- ALPHA\n'
             'COLUMN 2 \- BRAVO\n'
             'COLUMN 3 \- OTHERS\n\n'
             'EDITING THE FILE:\n'
             'ADD personnel at the bottom of respecitve column \(rank does not need to be in order\)\n\n'
             'NOTE: Fill in every detail \(RANK, DISPLAY\_NAME, NAME\_IN\_PS and NOR\)\. If NAME\_IN\_PS unknown, both NAME\_IN\_PS and DISPLAY\_NAME can be the same\.\n\n'
             'EDIT by just editing lol\n\n'
             'When done send the file back to me \U0001F601\n\n'
             '/exit to exit',
             parse_mode='MarkdownV2',
             disable_web_page_preview=True
    )
    
    return 1

# /ep [2nd] - saves FLIGHT_PERSONNEL FILE
async def edit_personnel_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # saves file in respective folder
    FILE = await update.message.effective_attachment.get_file()
    await FILE.download_to_drive('files_on_the_move/to_be_received/flight_personnel.xlsx')
    
    # runs program to sort and cache files
    edit_flight_personnel_files()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Successfully updated!\n'
             '/obtainfiles to see newly updated files'
    )

    return ConversationHandler.END

# MISC [EXIT] - when users want to exit out of page
async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text='Exit ok \U0001F44D',
                                   reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

if __name__ == '__main__':
    
    # load in SECRET API KEY and stores it in a variable known as API_KEY
    load_dotenv()
    API_KEY = os.getenv('API_KEY')

    # pee bot maker
    bot = ApplicationBuilder().token(API_KEY).build()

    # pee scheduler
    # updates the online sheets every 15 MINUTES
    # <<< from 10am to 10pm >>>
    update_pee_scheduler = bot.job_queue.run_repeating(run_pee_scheduler, datetime.timedelta(minutes=15), datetime.time(0, 0))

    # /start
    bot.add_handler(CommandHandler('start', start))

    # /help
    bot.add_handler(CommandHandler('help', help))

    # /tor
    bot.add_handler(CommandHandler('tor', tor))
    
    # /status
    bot.add_handler(CommandHandler('status', status))

    # /update
    bot.add_handler(CommandHandler('update', update_all))

    # /obtainfiles
    bot.add_handler(CommandHandler('obtainfiles', obtain_files))

    # /f [DATE]
    bot.add_handler(CommandHandler('f', print_ps))

    # /we [DATE]
    bot.add_handler(CommandHandler('we', print_weekend_duty))

    # /duty [START DATE] [END DATE]
    bot.add_handler(CommandHandler('duty', print_multiple_weekend_duty))

    # /ol
    bot.add_handler(CommandHandler('ol', print_override_ps_list))

    # /oa
    override_ps_add_handler = ConversationHandler(
        entry_points=[CommandHandler('oa', override_ps_add_start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, override_ps_add_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, override_ps_add_status)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, override_ps_add_date)]
        },
        fallbacks=[CommandHandler('exit', exit)]
    )

    bot.add_handler(override_ps_add_handler)

    # /ep
    edit_personnel_handler = ConversationHandler(
        entry_points=[CommandHandler('ep', edit_personnel_start)],
        states={
            1: [MessageHandler(filters.Document.ALL, edit_personnel_end)]
        },
        fallbacks=[CommandHandler('exit', exit)]
    )

    bot.add_handler(edit_personnel_handler)
    
    bot.run_polling()