import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from dotenv import load_dotenv
from pee_maker import *

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

# /oa
async def override_ps_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poo

if __name__ == '__main__':
    
    # load in SECRET API KEY and stores it in a variable known as API_KEY
    load_dotenv()
    API_KEY = os.getenv('API_KEY')

    # pee bot maker
    bot = ApplicationBuilder().token(API_KEY).build()

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
    
    bot.run_polling()
