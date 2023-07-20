import os
import psycopg2

# This file is for testing purposes.

# set environment variable from cli
# $env:DATABASE_URL = "postgresql://<USERNAME>:<ENTER-SQL-USER-PASSWORD>@<HOST>:<PORT>/defaultdb?sslmode=verify-full"


if __name__ == '__main__':
    # create connection
    connection = psycopg2.connect(os.environ['DATABASE_URL'])

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
