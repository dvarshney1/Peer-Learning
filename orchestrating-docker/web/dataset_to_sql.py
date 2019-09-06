import csv

def sql_list(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        my_list = list(reader)
    return my_list
