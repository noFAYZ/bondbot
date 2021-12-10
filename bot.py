from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import urllib
from selenium.common.exceptions import NoSuchElementException   
import time
import sqlite3
import os
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

lthreshold=45.0
jthreshold=40.0


##################################################
#
#               BondBot Schema
#
##################################################

class BondBot:

    def __init__(self, name, roi, price,hecprice, url,site):
        self.name = name
        self.price = price
        self.hecprice = hecprice
        self.roi = roi
        self.url = url
        self.site = site


    def get_bond_data(self):
        return {
            'name': self.name,
            'price': self.price,
            'hecprice': self.hecprice,
            'roi': self.roi,
            'url': self.url,
            'site':self.site
        }
    def get_bond_text(self):
        return "**ALERT** \n\nBond Name:\n" + self.name +"\n\nBond Price: \n"+ self.price +"\n\nHEC Price: \n"+ self.hecprice +"\n\nBond ROI: \n" + self.roi +"\n\nBond URL: \n" + self.url
    def check_update(self,bond):
        print()



##################################################
#
#               SQLite Database Utilities
#
##################################################
def create_table():
    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS bondData(bid INTEGER PRIMARY KEY AUTOINCREMENT,bname TEXT,bprice FLOAT,broi FLOAT,bhecprice FLOAT, burl TEXT, site INT);")
    conn.commit()
def drop_table():
    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()
    cur.execute("DROP TABLE bondData;")
    conn.commit()
def truncate_table():
    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM bondData;")
    conn.commit()
def add_bond(bond):
    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()
    froi=float(bond.roi.replace('%',''))
    cur.execute("select count(*) from bondData where bname=? and broi=?",(bond.name,froi))
    found=cur.fetchone()[0]

    if found==0:
        cur.execute("INSERT INTO bondData(bname,bprice,broi,bhecprice,burl,site) VALUES(?,?,?,?,?,?)",(bond.name,bond.price,bond.roi,bond.hecprice,bond.url,bond.site))
        conn.commit()
    else:
        cur.execute("UPDATE bondData SET bname=?,bprice=?,broi=?,bhecprice=?,burl=?,site=? WHERE bname=?",(bond.name,bond.price,bond.roi,bond.hecprice,bond.url,bond.name,bond.site))
        conn.commit()
    
def check_bond(bond):
    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()
    froi=float(bond.roi.replace('%',''))
    cur.execute("select count(*) from bondData where bname=? and broi=?",(bond.name,froi))
def print_table():

    conn = sqlite3.connect('bondbot.db')
    cur = conn.cursor()

    cur.execute("select * from bondData ")
    print(cur.fetchall())
    conn.commit()
###################################################
#
#               Update Function
#
####################################################

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f'Hi! {update.message.from_user.first_name}')
    update.message.reply_text('I will send you updates on the bonds you are interested in!')
    update.message.reply_text('To get started, type /bondname followed by the minimum threshold of the bond you are interested in!\nLike "/jade 20"')
    update.message.reply_text('Currently supported bond names are\n(1) /jade\n(2) /life.')



def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def remove_job_if_exists(update,context,name):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def life(update,context):
    lifet = float(context.args[0])
    global lthreshold
    lthreshold=lifet
    update.message.reply_text('Life Threshold set to {}'.format(lthreshold))
    context.bot.send_message(chat_id=update.message.chat_id,text='You will get Life Dao updates!')
    removed=remove_job_if_exists(update,context,'life')
    context.job_queue.run_repeating(lifeportal, 100,10,"life")
    print(context.job_queue.jobs())

def jade(update,context):
    jadet = float(context.args[0])
    global jthreshold
    jthreshold=jadet
    update.message.reply_text('Jade Threshold set to {}'.format(jthreshold))
    context.bot.send_message(chat_id=update.message.chat_id,text='You will get Jade Dao updates!')
    removed=remove_job_if_exists(update,context,'jade')
    context.job_queue.run_repeating(jadePortal, 100,10,name="jade")
    print(context.job_queue.jobs())

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)



def send_message(text):
    
    TOKEN="5089353143:AAEoLTXV_hZ4bHoPgqDsEd0rPpSGmWEtV_E"
    URL="https://api.telegram.org/bot{}".format(TOKEN)
    ParsedMessage= urllib.parse.quote_plus(text)
    requests.get(URL+"/sendMessage?chat_id=2129043892&text={}".format(ParsedMessage))



###################################################
#
#               Utility Functions
#
####################################################
def check_exists_by_class(elem,clas):
    try:
        elem.find_element_by_class_name(clas)
    except NoSuchElementException:
        return False
    return True

def check_exists_by_css(elem,clas):
    try:
        elem.find_element_by_css_selector(clas)
    except NoSuchElementException:
        return False
    return True



###################################################
#
#               Data Scraping & Notification
#
###################################################

def jadePortal(context):
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'normal'
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    driver = webdriver.Chrome('./chromedriver',options=options)

    driver.get("https://jadeprotocol.io/#/bonds")
    time.sleep(5)

    ro=1
    co=1

    for row in driver.find_elements_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[3]/div/table/tbody/tr"):
        cell = row.find_elements_by_tag_name("td")
        
        i=0
        for td in cell:
            if i==0:
                bname=td.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[3]/div/table/tbody/tr["+str(ro)+"]/td["+str(i+1)+"]/div[2]").text
            if i==1:
                bprice=td.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[3]/div/table/tbody/tr["+str(ro)+"]/td["+str(i+1)+"]/p").text
            elif i==2:
                broi=td.text
            elif i==3:
                bhecprice=td.text
            elif i==4:
                burl=td.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[3]/div/table/tbody/tr["+str(ro)+"]/td["+str(i+1)+"]/a").get_attribute("href")
            i+=1
        froi=float(broi.replace('%',''))
        print(jthreshold)
        if froi>jthreshold:
            bond = BondBot(bname, broi, bprice,bhecprice, burl,0)
            add_bond(bond)
            #print(bond.get_bond_text())
            send_message(bond.get_bond_text())
        ro+=1

         
    driver.close()            

def lifeportal(context):
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'normal'
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--window-size=1366, 768")
    # assert options.headless 
    driver = webdriver.Chrome('./chromedriver',options=options)

    driver.get("https://lifedao.finance/#/mints")
    time.sleep(15)
    table="//*[@id='root']/div/div[4]/div[3]/div/div[3]/div/table/tbody"

    ro=1
    co=1

    for row in driver.find_elements_by_xpath(table+"/tr"):
        cell = row.find_elements_by_tag_name("td")        
        i=0
        for td in cell:
            if i==0:
                bname=td.find_element_by_xpath(table+"/tr["+str(ro)+"]/td["+str(i+1)+"]/div[2]/p").text
            elif i==1:
                bprice=td.find_element_by_xpath(table+"/tr["+str(ro)+"]/td["+str(i+1)+"]/p").text.rstrip()
            elif i==2:
                broi=td.find_element_by_xpath(table+"/tr["+str(ro)+"]/td["+str(i+1)+"]/p").text
            elif i==3:
                bhecprice=td.find_element_by_xpath(table+"/tr["+str(ro)+"]/td["+str(i+1)+"]/p").text
            elif i==4:
                burl=td.find_element_by_xpath(table+"/tr["+str(ro)+"]/td["+str(i+1)+"]/a").get_attribute("href")
            i+=1
        
        froi=float(broi.replace('%',''))
        print(lthreshold)
        if froi>lthreshold:
            bond = BondBot(bname, broi, bprice,bhecprice, burl,0)
            add_bond(bond)
            
            send_message(bond.get_bond_text())
        # bond = BondBot(bname, broi, bprice,bhecprice, burl)
        ro+=1

    driver.close()


def jobscheduler(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text='Setting a timer for 1 minute!')

    context.job_queue.run_repeating(lifeportal, 100,first=10)
    context.job_queue.run_repeating(jadePortal, 100,first=10)

###################################################
#
#               Main Process
#
###################################################


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("5089353143:AAEoLTXV_hZ4bHoPgqDsEd0rPpSGmWEtV_E", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("life", life))
    dp.add_handler(CommandHandler("jade", jade))
    dp.add_handler(CommandHandler("chalo", jobscheduler))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    create_table()
    # starttime = time.time()
    # while True:
    #     #jadePortal()
    #     lifeportal()
    #     time.sleep(100.0 - ((time.time() - starttime) % 100.0))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    


if __name__ == '__main__':
    main()




# truncate_table()


# b2=BondBot("BaB",230,21312,1221,"http://asuhduah.com/",1)
# # truncate_table()

# add_bond(b2)