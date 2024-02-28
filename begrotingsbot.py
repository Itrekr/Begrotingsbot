#!/usr/bin/env python3

import logging, csv, os, datetime, configparser, calendar, asyncio, aiofiles
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from datetime import date

# Load Telegram Config from environment variables or a secure source
config = configparser.ConfigParser()
config.read('config.ini')

TELEGRAM_BOT_TOKEN = config['Telegram']['BotToken']
authorized_user_ids_str = config['Telegram']['AuthorizedUserIds']
authorized_user_ids_str = authorized_user_ids_str.strip('[]')  # Remove the leading and trailing square brackets
AUTHORIZED_USER_IDS = [int(user_id) for user_id in authorized_user_ids_str.split(',')]  # Split on comma and convert to integers

# Dagen calculator
def Dagen_calculator():
    vandaag = date.today()
    eom = datetime.date(vandaag.year, vandaag.month, calendar.monthrange(vandaag.year, vandaag.month)[-1])
    dagen_tot_eom = eom - vandaag
    output = dagen_tot_eom.days
    return output + 1

# Time config
def days_till_end_of_month():
    today = date.today()
    eom = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[-1])
    days_till_eom = eom - today
    return days_till_eom.days + 1

async def af(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        try:
            prijs = "{:.2f}".format(float(context.args[0]))
            omschrijving = ' '.join(context.args[1:-1])
            verwerkt = context.args[-1].lower() == "ja"
            user_name = 'Oscar' if update.effective_chat.id == 1341642988 else 'Sara'  # Replace 1341642988 with the actual chat ID of Oscar.
            entry = f"Af,{prijs},{omschrijving.replace(',', '')},{verwerkt},{user_name},{date.today()}\n"
            with open('begroting.csv', 'a') as begroting:
                begroting.write(entry)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"{omschrijving} voor €{prijs} is toegevoegd{' en hoeft niet meer te worden verwerkt' if verwerkt else ' en moet nog worden teruggegeven van de gezamenlijke'}.")

        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Er is iets misgegaan.\nControleer of je alles juist hebt geschreven (bijv. /af 2.50 Appel Ja)\nError: {e}")

af_handler = CommandHandler('af', af)

async def bij(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        try:
            trueprijs = "{:.2f}".format(0 - float(context.args[0]))
            printprijs = "{:.2f}".format(float(context.args[0]))
            omschrijving = ' '.join(context.args[1:-1])
            verwerkt = context.args[-1].lower() == "ja"
            user_name = 'Oscar' if update.effective_chat.id == 1341642988 else 'Sara'  # Replace 1341642988 with the actual chat ID of Oscar.
            entry = f"Bij,{trueprijs},{omschrijving.replace(',', '')},{verwerkt},{user_name},{date.today()}\n"
            with open('begroting.csv', 'a') as begroting:
                begroting.write(entry)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"{omschrijving} voor €{printprijs} is toegevoegd{' en hoeft niet meer te worden verwerkt' if verwerkt else ' en moet nog worden teruggegeven van de gezamenlijke'}.")

        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Er is iets misgegaan.\nControleer of je alles juist hebt geschreven (bijv. /bij 2.50 Appel Ja)\nError: {e}")
bij_handler = CommandHandler('bij', bij)

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        with open('begroting.csv') as begroting:
            reader = csv.reader(begroting)
            next(reader, None)  # Skip the header row
            total_price = sum(float(row[1]) for row in reader if row[1])

        percentage = "{:.2f}".format((total_price / 400) * 100)
        remaining_budget = 400 - total_price
        days_remaining = Dagen_calculator()
        daily_budget = remaining_budget / days_remaining

        budget_info = (
            f"Momenteel hebben we {percentage}% van ons budget uitgegeven wat gelijk staat aan een bedrag van €{total_price:.2f}.\n\n"
            f"Dat betekent dat we nog €{remaining_budget:.2f} te besteden hebben deze maand.\n\n"
            f"Deze maand heeft nog {days_remaining} dagen. Dus in principe kunnen we nog €{daily_budget:.2f} euro per dag uitgeven zonder over budget te gaan."
        )

        await context.bot.send_message(chat_id=update.effective_chat.id, text=budget_info)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

budget_handler = CommandHandler('Budget', budget)

async def verwerkt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        with open("begroting.csv", "rt") as begroting:
            data = begroting.read()

        data = data.replace('False', 'True')

        with open("begroting.csv", "wt") as begroting:
            begroting.write(data)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Terugbetalingen zijn verwerkt!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

verwerkt_handler = CommandHandler('Verwerkt', verwerkt)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        with open("begroting.csv") as begroting:
            header = begroting.readline()  # Read the first line of the file

        with open("begroting.csv", "w") as begroting:
            begroting.write(header)  # Write the header back to the file

        await context.bot.send_message(chat_id=update.effective_chat.id, text="👍")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

reset_handler = CommandHandler('Reset', reset)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Hoi! Ik ben Begrotingsbot. Ik kan wel rekenen en shit onthouden. Leuk he? "
        "Ik wil het met liefde voor je doen, maar dan moet je wel mijn taal spreken.\n\n"
        "Mijn belangrijkste commands zijn /bij en /af. Dat is voor bedragen die bij ons budget "
        "komen of er vanaf moeten worden gehaald. Als je iets gekocht hebt van de gezamelijke rekening "
        "typ je bijvoorbeeld:\n"
        "/af 2.50 Appels Ja\n\n"
        "Het is belangrijk dat je centen onderscheidt met een punt en dat je niet vergeet te vermelden "
        "of het bedrag al verwerkt is (ja/nee). Als je het nog terug moet krijgen van de gezamelijke "
        "schrijf je daar dus 'Nee'. Een stink kan de was doen.\n\n"
        "Je hebt ook nog andere commands zoals /terug die laat zien hoe veel iedereen nog terug krijgt "
        "en /bon die de huidige betalingen in een pdf'je zet. Ook /budget, /verwerkt en /reset werken al, "
        "maar die wijzen gelukkig zichzelf! Joe!"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

help_handler = CommandHandler('Help', help_command)

async def terug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        totaal_sara = 0.0
        totaal_oscar = 0.0
        async with aiofiles.open('begroting.csv', mode='r', encoding='utf-8') as begroting:
            # Skip the header
            await begroting.readline()
            async for line in begroting:
                row = line.strip().split(',')
                if row[3].lower() == "false":  # Check if 'verwerkt' is False
                    prijs = float(row[1])
                    if row[4].lower() == "sara":
                        totaal_sara += prijs
                    elif row[4].lower() == "oscar":
                        totaal_oscar += prijs
        
        message = (f"Oscar moet nog €{totaal_oscar:.2f} terugkrijgen van de gezamelijke.\n\n"
                   f"Sara moet nog €{totaal_sara:.2f} terugkrijgen van de gezamelijke.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")


terug_handler = CommandHandler('Terug', terug_command)

async def bon_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        process = await asyncio.create_subprocess_exec(
            'cp', 'begroting.csv', 'bon.md'
        )
        await process.wait()
        process = await asyncio.create_subprocess_exec(
            'sed', '-i', '-e', '2 i --\|--\|--\|--\|--', '-e', 's/,/\|/g', '-e', 's/True/Ja/g', '-e', 's/False/Nee/g', 'bon.md'
        )
        await process.wait()
        process = await asyncio.create_subprocess_exec(
            'compiler', 'bon.md'
        )
        await process.wait()
        with open('bon.pdf', 'rb') as document:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=document)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

bon_handler = CommandHandler('Bon', bon_command)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        file_name = str(context.args[0])

        # Copy the file
        process = await asyncio.create_subprocess_exec(
            'cp', 'begroting.csv', f'{file_name}.md'
        )
        await process.wait()

        # Copy the file again with a different extension
        process = await asyncio.create_subprocess_exec(
            'cp', 'begroting.csv', f'{file_name}.csv'
        )
        await process.wait()

        # Modify the file using sed
        process = await asyncio.create_subprocess_exec(
            'sed', '-i', '-e', '2 i --\|--\|--\|--\|--', '-e', 's/,/\|/g', '-e', 's/True/Ja/g', '-e', 's/False/Nee/g', f'{file_name}.md'
        )
        await process.wait()

        # Call the compiler
        process = await asyncio.create_subprocess_exec(
            'compiler', f'{file_name}.md'
        )
        await process.wait()

        # Send the document
        with open(f'{file_name}.pdf', 'rb') as document:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=document)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

export_handler = CommandHandler('Export', export_command)

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You need to provide a file name.")
            return
        file_name = str(context.args[0])
        file_path = f'{file_name}.pdf'
        try:
            with open(file_path, 'rb') as document:  # use the built-in open function
                await context.bot.send_document(chat_id=update.effective_chat.id, document=document, filename=file_path)
        except FileNotFoundError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Die pdf heb ik niet! Sorry!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Jij woont niet bij ons. Opzouten!")

download_handler = CommandHandler('Download', download_command)

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.effective_chat.id)
    if update.effective_chat.id in AUTHORIZED_USER_IDS:
        print("Authorized.")
    else:
        print("Unauthorized.")

debug_handler = CommandHandler('Debug', debug_command)

def build_application():
    # Create an Application instance
    application = ApplicationBuilder().token(config['Telegram']['BotToken']).build()

    # Add handlers
    application.add_handler(CommandHandler('Af', af))
    application.add_handler(CommandHandler('Bij', bij))
    application.add_handler(CommandHandler('Budget', budget))
    application.add_handler(CommandHandler('Verwerkt', verwerkt))
    application.add_handler(CommandHandler('Reset', reset))
    application.add_handler(CommandHandler('Help', help_command))
    application.add_handler(CommandHandler('Terug', terug_command))
    application.add_handler(CommandHandler('Bon', bon_command))
    application.add_handler(CommandHandler('Export', export_command))
    application.add_handler(CommandHandler('Download', download_command))
    application.add_handler(CommandHandler('Debug', debug_command))

    # Schedule the reminders
    # application.job_queue.run_daily(send_daily_reminders, datetime.time(hour=9, minute=0, second=0))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    build_application()
