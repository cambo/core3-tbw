import sqlite3
from datetime import datetime
from pathlib import Path

class Sql:
    def __init__(self):
        self.home = str(Path.home())
        self.data_path = self.home+'/core3-tbw/core/data/tbw.db'

        
    def open_connection(self):
        self.connection = sqlite3.connect(self.data_path)
        self.cursor = self.connection.cursor()
    
    
    def close_connection(self):
        self.cursor.close()
        self.connection.close()
    
    
    def commit(self):
        return self.connection.commit()


    def execute(self, query, args=[]):
        return self.cursor.execute(query, args)


    def executemany(self, query, args):
        return self.cursor.executemany(query, args)


    def fetchone(self):
        return self.cursor.fetchone()


    def fetchall(self):
        return self.cursor.fetchall()


    def setup(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS blocks (id varchar(64), timestamp int, reward int, totalFee bigint, height int, processed_at varchar(64) null)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS voters (address varchar(36), u_balance bigint, p_balance bigint, share float )")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS transactions (address varchar(36), amount varchar(64), id varchar(64), processed_at varchar(64) )")
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS delegate_rewards (address varchar(36), u_balance bigint, p_balance bigint )")
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS staging (address varchar(36), payamt bigint, msg varchar(64), processed_at varchar(64) null )")
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS exchange (initial_address varchar(36), payin_address varchar(36), exchange_address varchar(64), payamt bigint, exchangeid varchar(64), processed_at varchar(64) null )")

        self.connection.commit()


    def store_exchange(self, i_address, pay_address, e_address, amount, exchangeid):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        exchange=[]
        exchange.append((i_address, pay_address, e_address, amount, exchangeid, ts))
        self.executemany("INSERT INTO exchange VALUES (?,?,?,?,?,?)", exchange)
        self.commit()
    
    
    def stage_payment(self, address, amount, msg):
        staging=[]

        staging.append((address, amount, msg, None))

        self.executemany("INSERT INTO staging VALUES (?,?,?,?)", staging)

        self.commit()


    def store_blocks(self, blocks):
        newBlocks=[]

        for block in blocks:
            self.cursor.execute("SELECT id FROM blocks WHERE id = ?", (block[0],))

            if self.cursor.fetchone() is None:
                newBlocks.append((block[0], block[1], block[2], block[3], block[4], None))

        self.executemany("INSERT INTO blocks VALUES (?,?,?,?,?,?)", newBlocks)

        self.commit()


    def store_voters(self, voters, share):
        newVoters=[]

        for voter in voters:
            self.cursor.execute("SELECT address FROM voters WHERE address = ?", (voter[0],))

            if self.cursor.fetchone() is None:
                newVoters.append((voter[0], 0, 0, share))

        self.executemany("INSERT INTO voters VALUES (?,?,?,?)", newVoters)

        self.commit()


    def store_delegate_rewards(self, delegate):
        newRewards=[]

        for d in delegate:
            self.cursor.execute("SELECT address FROM delegate_rewards WHERE address = ?", (d,))

            if self.cursor.fetchone() is None:
                newRewards.append((d, 0, 0))

        self.executemany("INSERT INTO delegate_rewards VALUES (?,?,?)", newRewards)

        self.commit()


    def store_transactions(self, tx):
        newTransactions=[]
        
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for t in tx:
            self.cursor.execute("SELECT id FROM transactions WHERE id = ?", (t[2],))
            
            if self.cursor.fetchone() is None:
                newTransactions.append((t[0], t[1], t[2], ts))
                
        self.executemany("INSERT INTO transactions VALUES (?,?,?,?)", newTransactions)
        
        self.commit()


    def mark_processed(self, block, initial="N"):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if initial == "N":
            self.cursor.execute(f"UPDATE blocks SET processed_at = '{ts}' WHERE height = '{block}'")
        else:
            self.cursor.execute(f"UPDATE blocks SET processed_at = '{ts}' WHERE height <= '{block}'")
        
        self.commit()


    def blocks(self):
        return self.cursor.execute("SELECT * FROM blocks")


    def last_block(self): 
        return self.cursor.execute("SELECT height from blocks ORDER BY height DESC LIMIT 1")
    
    
    def processed_blocks(self):
        return self.cursor.execute("SELECT * FROM blocks WHERE processed_at NOT NULL")


    def unprocessed_blocks(self):
        return self.cursor.execute("SELECT * FROM blocks WHERE processed_at IS NULL ORDER BY height")


    def staged_payment(self, lim=40, multi='N'):
        if multi is 'N':
            return self.cursor.execute(f"SELECT rowid, * FROM staging WHERE processed_at IS NULL LIMIT {lim}")
        else:
            return self.cursor.execute(f"SELECT rowid, * FROM staging WHERE processed_at IS NULL")
            

    def process_staged_payment(self, rows):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')		
        for i in rows:
            self.cursor.execute(f"UPDATE staging SET processed_at = '{ts}' WHERE rowid = {i}")
        self.commit()

    
    def delete_staged_payment(self):
        self.cursor.execute("DELETE FROM staging WHERE processed_at NOT NULL")     
        self.commit()

    
    def delete_test_exchange(self,p_in,p_out,amount):
        self.cursor.execute(f"DELETE FROM exchange WHERE initial_address = '{p_in}' AND payin_address = '{p_out}' AND payamt = '{amount}'")
        self.commit()
    
    
    def delete_transaction_record(self, txid):
        self.cursor.execute(f"DELETE FROM transactions WHERE id = '{txid}'")
        self.commit()

        
    def voters(self):
        return self.cursor.execute("SELECT * FROM voters ORDER BY u_balance DESC")


    def rewards(self):
        return self.cursor.execute("SELECT * FROM delegate_rewards")


    def transactions(self):
        return self.cursor.execute("SELECT * FROM transactions ORDER BY processed_at DESC LIMIT 1000")


    def update_voter_balance(self, address, balance):
        self.cursor.execute(f"UPDATE voters SET u_balance = u_balance + {balance} WHERE address = '{address}'")
        self.commit()


    def update_delegate_balance(self, address, balance):
        self.cursor.execute(f"UPDATE delegate_rewards SET u_balance = u_balance + {balance} WHERE address = '{address}'")
        self.commit()


    def update_voter_paid_balance (self, address):
        self.cursor.execute(f"UPDATE voters SET p_balance = p_balance + u_balance WHERE address = '{address}'")
        self.cursor.execute(f"UPDATE voters SET u_balance = u_balance - u_balance WHERE address = '{address}'")
        self.commit()


    def update_delegate_paid_balance (self, address, amount):
        self.cursor.execute(f"UPDATE delegate_rewards SET p_balance = p_balance + {amount} WHERE address = '{address}'")
        self.cursor.execute(f"UPDATE delegate_rewards SET u_balance = u_balance - {amount} WHERE address = '{address}'")
        self.commit()

    
    def update_voter_share(self, address, share):
        self.cursor.execute("UPDATE voters SET share = {0} WHERE address = '{1}'".format(share, address))
        self.commit()


    def get_voter_share(self, address):
        return self.cursor.execute("SELECT share FROM voters WHERE address = '{0}'".format(address))
