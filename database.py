import sqlite3
import datetime

class connection:
    def __init__(self, fileName='example.db'):
        self.con = sqlite3.connect(fileName, check_same_thread=False)
        self.cur = self.con.cursor()
        self.createTable()  # Ensure the table is created when initializing the connection
    
    def insertData(self, data):
        currentTime = datetime.datetime.now()
        self.cur.execute("INSERT INTO sensorData (data, time) VALUES (?, ?)", (data, currentTime))
        # Save (commit) the changes
        self.con.commit()

    def createTable(self):
        # Create table if it doesn't exist
        self.cur.execute('''CREATE TABLE IF NOT EXISTS sensorData
                            (data REAL, time TIMESTAMP)''')

    def printAll(self):
        for row in self.cur.execute("SELECT * FROM sensorData"):
            print(row)

    def close(self):
        self.con.close()

if __name__=="__main__":
    # USED FOR DEUBGGING PURPOSES
    a = connection()
    a.printAll()
    a.close()