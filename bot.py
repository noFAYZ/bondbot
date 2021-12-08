from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import urllib
from selenium.common.exceptions import NoSuchElementException   
import time
import sqlite3
import os


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
def send_message(text):
    
    TOKEN="5044795460:AAFBCEoYTR3PtcGu_FKZbK7wlz1kOwi1ZzI"
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

def jadePortal():
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'normal'
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),options=options)

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
        if froi>50.0:
            bond = BondBot(bname, broi, bprice,bhecprice, burl,0)
            add_bond(bond)
            #print(bond.get_bond_text())
            send_message(bond.get_bond_text())
        ro+=1

         
    driver.close()            

def lifeportal():
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'normal'
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--headless")
    options.add_argument("--window-size=1366, 768")
    # assert options.headless 
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),options=options)

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
        if froi>50.0:
            bond = BondBot(bname, broi, bprice,bhecprice, burl,0)
            add_bond(bond)
            
            send_message(bond.get_bond_text())
        # bond = BondBot(bname, broi, bprice,bhecprice, burl)
        ro+=1

    driver.close()




###################################################
#
#               Main Process
#
###################################################
if __name__ == '__main__':
    create_table()
    starttime = time.time()
    while True:
        jadePortal()
        lifeportal()
        time.sleep(300.0 - ((time.time() - starttime) % 300.0))

# truncate_table()


# b2=BondBot("BaB",230,21312,1221,"http://asuhduah.com/",1)
# # truncate_table()

# add_bond(b2)