import os
import psycopg2
from dotenv import load_dotenv

# This file is for testing purposes.

if __name__ == '__main__':
    # load environment variables
    load_dotenv()

    # create connection
    connection = psycopg2.connect(os.environ.get('DATABASE_URL'))

    # create a cursor and execute query
    cursor = connection.cursor()
    cursor.execute("DELETE FROM public.\"User\";")

    connection.commit()

    print('Delete data done!')

    # close the connection
    cursor.close()
    connection.close()


# del os.environ['DATABASE_URL']
# print(os.getenv('DATABASE_URL'))
