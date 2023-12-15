import pandas as pd

# Sample data
data = {
    'Name': ['khant si thu', 'aung thet paing', 'kaung khant kyaw'],
    'BatchName': ['HND-45', 'HND-45', 'HND-45'],
    'TimeTable': ['Mon - Fri (8 am - 11:10 am)', 'Mon - Fri (12 am - 3:10 am)', 'Mon - Fri (4 am - 6:10 am)']
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save DataFrame to CSV file
df.to_csv('user_info.csv', index=False)
