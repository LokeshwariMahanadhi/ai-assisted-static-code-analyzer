import math
import os  # Unused import

def calculate_data(items, user_list=[]):  # Mutable default
    temp_calc = 100  # Unused variable
    id = "custom_id"  # Shadowed builtin 'id'
    
    config = {
        "timeout": 30,
        "timeout": 60,  # Duplicate dict key
    }
    
    try:
        total = 0
        for item in items:
            total += item
        return total
        print("This line is unreachable!")  # Unreachable code
    except:  # Bare except
        return None

def check_value(val):
    if val == None:  # Comparison to None
        return False
    if val == True:  # Comparison to True
        return True
    return False
