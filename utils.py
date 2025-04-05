from datetime import datetime

def get_day_weekday_toString(date):
    # Get weekday (0 = Monday, 1 = Tuesday, ..., 6 = Wednesday)
    day_of_week = date.weekday()
    day_month = date.day
    # List to convert number to nameOfDay
    days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    day_name = days[day_of_week]
    return (f"{day_name} {day_month}")
    