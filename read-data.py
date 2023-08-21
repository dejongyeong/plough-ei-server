import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# This file is for downloading all user information after the event.

if __name__ == '__main__':
    # load environment variables
    load_dotenv()

    # create connection
    connection = psycopg2.connect(os.environ.get('DATABASE_URL'))

    # create a cursor and execute query
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM public.\"User\";")

    # read data into a pandas dataframe
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    # close the connection
    cursor.close()
    connection.close()

    # output into csv file
    filename = 'ploughing-championship-participants.csv'
    if os.path.exists(filename):
        df.to_csv(filename, index=False, mode='w')
    else:
        df.to_csv(filename, index=False)

    print('Data output to ' + filename)


# del os.environ['DATABASE_URL']
# print(os.getenv('DATABASE_URL'))
