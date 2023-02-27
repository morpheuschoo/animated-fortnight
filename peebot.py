import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler
from pee_maker import *
from pee_scheduler import download_adw_and_me
from pytz import timezone
from dotenv import load_dotenv

# tells you when the programme starts / stops (in console)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="/help - tells you what the bot can do")

# /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='NOTE: [DATE] will be in [DD][MM][YY] format\n'
                                                                          '(eg 20th Jan 2023 will be written as 200123)\n')

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Stuff you can do with the bot:\n\n'
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

# /tor
async def tor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='FOR TO:\n'
                                        '**Check your OSN email**\n\n'
                                        'https://docs.google.com/spreadsheets/d/1whbTO1tvIa2FpMyVTVTJZWsRjWRIqVPzPAGY4BGfrSk/edit?usp=drivesdk')

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='FOR G1, G2 and G3A:\n\n'
                                        'https://docs.google.com/spreadsheets/d/1TwTIG7XdT1RRWzm8XCtbuWyKcMMdXwGr/edit')
    
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='FOR literally everything else:\n\n'
                                        'https://docs.google.com/file/d/1rXLXxWMSpb8hU_BRuI87jv7wS04tB6yD/edit?usp=docslist_api')

# /f [DATE]
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
        
        # open username_ref as a dict
        # username_ref matches the user's username to their rank + name printed in the parade state
        with open('references/username_ref.json') as username_ref_json:
            username_ref_dict = load(username_ref_json)

        # load in all the stuff required to print parade state
        load_ME_sheet(DATE)
        update_adw(DATE)
        categorise_ps()

        known_ps, unknown_ps = front_ps(DATE, username_ref_dict[update.message.from_user.username], "alpha")

        # sends the parade state
        await context.bot.send_message(chat_id=update.effective_chat.id, text = f'{known_ps}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{middle_ps(DATE, 5, 7, 5, "alpha")}'
                                                                                f'---------------------------------------------------\n\n'
                                                                                f'{end_ps(DATE)}')

        # if there are unknowns in parade state, unknowns will be listed and sent in another message
        if unknown_ps != "":
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'UNKNOWN:\n{unknown_ps}')
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in a valid date (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return

# /we [DATE]
async def print_weekend_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # ensures that both dates are numeric and are 6 numbers long
        if not re.search('[0-9]{6}', start_date) or not re.search('[0-9]{6}', end_date):
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Dates should be 6 numbers long -_-')
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{duty_compiler(update.message.from_user.username, start_date, end_date)}')
    
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The bot is broken or you didnt type in valid dates (uh oh)')
        await context.bot.send_message(chat_id=update.effective_chat.id, text='\U0001F613')
        return
    
# /ol
async def print_override_ps_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open('override/override_ps.json') as override_ps_json:
            override_ps_list = load(override_ps_json)
        
        everyone_list = load_163()

        combined = {}

        # iterrates through the override ps list
        # creates a dictionary:
        # KEY: name in parade state
        # VALUE: [0]-rank + displayed name / [1 and above]-status with start date and end date
        for x in override_ps_list:
            for y in everyone_list:
                if x['NAME_IN_PS'] == y['NAME_IN_PS']:
                    if x['NAME_IN_PS'] not in combined:
                        combined[x['NAME_IN_PS']] = [y['RANK'] + ' ' + y['DISPLAY_NAME'] if y['RANK'] != 'NIL' else y['DISPLAY_NAME']]
                    
                    combined[x['NAME_IN_PS']].append(f'{x["START_DATE"]} to {x["END_DATE"]} ({x["STATUS_IN_PS"]})')

        print_combined = f'<<<OVERRIDE LIST>>>\n\n'

        for x in combined.values():
            print_combined += f'{x[0]}:\n' + '\n'.join(x[1:]) + '\n\n'

        await context.bot.send_message(chat_id=update.effective_chat.id, text=print_combined)
            
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Override list is empty')

# ***DICTIONARY FOR /oa***
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
                                   reply_markup=ReplyKeyboardMarkup(keyboard, input_field_placeholder='Choose personnel'))

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
                                   reply_markup=ReplyKeyboardMarkup(keyboard, input_field_placeholder='Select status'))

    return 2

# /oa [3rd] - saves STATUS and asks for START DATE to END DATE
async def override_ps_add_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # saves the status, clearing up any input error
    # (eg. trailing, leading whitespaces or whitespaces beside '/')
    temp_override_ps_dict['STATUS_IN_PS'] = re.sub('\s*/\s*', '/', update.message.text.upper().strip())
    
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text='Input: [START_DATE] [END_DATE]\n'
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

# # /or [1st] - asks for NAME
# async def override_ps_remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     everyone_list = load_163()

#     with open('override/overrie_ps.json') as override_ps_json:
#         override_ps_list = load(override_ps_json)
    
#     override_ps_set_ran = set()

#     for x in everyone_list:
#         for y in override_ps_list:
#             if x['NAME_IN_PS'] == y['NAME_IN_PS']:
#                 override_ps_set_ran.add(x['RANK'] + ' ' + x['DISPLAY_NAME'] if x['RANK'] != 'NIL' else x['DISPLAY_NAME'])


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
    # <<< from 10am to 5pm >>>
    update_online_sheets = bot.job_queue.run_repeating(load_ME_sheet, datetime.timedelta(minutes=15), datetime.time(2, 0), datetime.time(9, 0))

    # /start
    bot.add_handler(CommandHandler('start', start))

    # /help
    bot.add_handler(CommandHandler('help', help))

    # /tor
    bot.add_handler(CommandHandler('tor', tor))

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
    
    bot.run_polling()