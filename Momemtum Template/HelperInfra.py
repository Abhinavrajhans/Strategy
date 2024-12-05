from datetime import datetime, timedelta
import calendar
import numpy as np
import pandas as pd

def get_target_date(start_date: datetime, pattern: str, query_type: int) -> datetime:
    """
    Calculate target date based on pattern string and query type.
    
    Args:
        start_date (datetime): Starting date
        pattern (str): Pattern string based on query_type
            Type 1: "M/D/W" where:
                M: Month offset (can be negative, 0=current, -1=previous month, etc.)
                D: Day of week (1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri)
                W: Week number (1=First, 2=Second, 3=Third, L=Last)
            Type 2: "MF" or "ML" where:
                M: Month offset (can be negative, 0=current, -1=previous month, etc.)
                F: First day of month
                L: Last day of month
        query_type: 1 or 2 to specify the pattern type
            
    Example patterns:
        Type 1: "0/1/1" - First Monday of current month
        Type 1: "-3/5/L" - Last Friday of 3 months ago
        Type 2: "-1F" - First day of previous month
        Type 2: "1L" - Last day of next month
        
    Returns:
        datetime: Calculated target date
    """
    if query_type not in [1, 2]:
        raise ValueError("Query type must be 1 or 2")
        
    # Helper function to calculate target month
    def get_adjusted_year_month(year: int, month: int, offset: int) -> tuple:
        month += offset
        
        while month <= 0:
            year -= 1
            month += 12
        while month > 12:
            year += 1
            month -= 12
            
        return year, month

    if query_type == 1:
        try:
            month_offset, day_of_week, week_pos = pattern.split('/')
            month_offset = int(month_offset)
            day_of_week = int(day_of_week) - 1  # Convert 1-5 to 0-4
            
            if not (1 <= int(day_of_week) + 1 <= 5):
                raise ValueError("Day must be between 1-5 (Mon-Fri)")
            if week_pos not in ['1', '2', '3', 'L']:
                raise ValueError("Week must be 1, 2, 3, or L")
                
        except ValueError as e:
            raise ValueError(f"Invalid Type 1 pattern format. Error: {str(e)}")
        
        # Calculate target month
        year, month = get_adjusted_year_month(start_date.year, start_date.month, month_offset)
        target_month = datetime(year, month, 1)
        
        # Get calendar for target month
        c = calendar.monthcalendar(target_month.year, target_month.month)
        
        # Find all occurrences of the specified day
        day_occurrences = []
        for week in c:
            if week[day_of_week] != 0:
                day_occurrences.append(week[day_of_week])
        
        # Get the target day based on week position
        if week_pos == 'L':
            target_day = day_occurrences[-1]
        else:
            week_index = int(week_pos) - 1
            target_day = day_occurrences[week_index] if len(day_occurrences) > week_index else day_occurrences[-1]
        
        return target_month.replace(day=target_day)
        
    else:  # query_type == 2
        try:
            if not (pattern.endswith('F') or pattern.endswith('L')):
                raise ValueError("Type 2 pattern must end with F (First) or L (Last)")
            
            month_offset = int(pattern[:-1])
            is_first_day = pattern.endswith('F')
            
        except ValueError as e:
            raise ValueError(f"Invalid Type 2 pattern format. Error: {str(e)}")
        
        # Calculate target month
        year, month = get_adjusted_year_month(start_date.year, start_date.month, month_offset)
        
        if is_first_day:
            # First day of month
            return datetime(year, month, 1)
        else:
            # Last day of month
            return datetime(year, month, calendar.monthrange(year, month)[1])
        


def calculate_historical_volatility(equity_data, lookback_period=126):
    log_returns = np.log(equity_data['Close'] / equity_data['Close'].shift(1))
    rolling_std = log_returns.rolling(window=lookback_period).std()
    volatility = rolling_std * np.sqrt(126)
    volatility = pd.Series(volatility, index=equity_data.index).fillna(0.25)
    return { 'volatility': volatility}

def get_data(file, columns):
    file_extension = file.split('.')[-1]
    if file_extension == 'pkl':
        df = pd.read_pickle(file)
    elif file_extension == 'csv':
        df = pd.read_csv(file)
    elif file_extension == 'xlsx':
        df = pd.read_excel(file)
    
    # Corrected: Avoid inplace=True, just assign the result to df
    df = df.rename(columns=columns)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def last_friday_of_previous_month(year, month):
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)

    offset = (last_date.weekday() - 3) % 7  # 3 = Thursday
    last_thursday_date = last_date - timedelta(days=offset)
    return last_thursday_date + timedelta(days=1)  # Adjusting to Friday if needed



def last_thursday(year, month):
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)

    offset = (last_date.weekday() - 3) % 7  # 3 = Thursday
    last_thursday_date = last_date - timedelta(days=offset)
    return last_thursday_date


# Example usage
if __name__ == "__main__":
    start_date = datetime(2024, 11, 20)
    
    print("Type 1 Queries:")
    type1_patterns = [
        "0/1/1",   # First Monday of current month
        "-1/5/L",  # Last Friday of previous month
        "-2/3/2",  # Second Wednesday of 2 months ago
        "-3/5/L",  # Last Friday of 3 months ago
    ]
    
    for pattern in type1_patterns:
        result = get_target_date(start_date, pattern, 1)
        print(f"Pattern {pattern}: {result.strftime('%Y-%m-%d')}")
    
    print("\nType 2 Queries:")
    type2_patterns = [
        "-1F",  # First day of previous month
        "-1L",  # Last day of previous month
        "0F",   # First day of current month
        "0L",   # Last day of current month
        "1F",   # First day of next month
        "1L",   # Last day of next month
        "-3F",  # First day of 3 months ago
        "-3L",  # Last day of 3 months ago
    ]
    
    for pattern in type2_patterns:
        result = get_target_date(start_date, pattern, 2)
        print(f"Pattern {pattern}: {result.strftime('%Y-%m-%d')}")