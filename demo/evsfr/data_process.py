import os
import pandas as pd
from openpyxl import load_workbook
import shutil

# copy the file from the original location to the new location
src_file = "demo/evsfr/source/ieee39_evsfr.xlsx"
dst_file = "demo/evsfr/out/ieee39_ev_f.xlsx"
shutil.copyfile(src_file, dst_file)

# rename the copied file
new_dst_file = "demo/evsfr/out/ieee39_ev_f.xlsx"
shutil.move(dst_file, new_dst_file)

# read the CSV file into a dataframe
df = pd.read_csv('demo/evsfr/source/ieee39_ev_f_out.csv')

# load the existing Excel file
book = load_workbook(new_dst_file)

# create a new sheet for the dataframe
writer = pd.ExcelWriter(new_dst_file, engine='openpyxl') 
writer.book = book
df.to_excel(writer, sheet_name='O_His')

# save the changes
writer.save()

# Read CSV file into a pandas DataFrame
# # Read CSV file into a pandas DataFrame
# input_path = os.path.join(os.getcwd(), 'demo/evsfr/source/ieee39_ev_fict_out.csv')
# df = pd.read_csv(input_path)

# # Create a Pandas Excel writer using xlsxwriter as the engine
# out_path = os.path.join(os.getcwd(), 'demo/evsfr/out/ieee39_ev_fict.xlsx')
# writer = pd.ExcelWriter(out_path, engine='xlsxwriter')

# # Write DataFrame to a sheet named 'Sheet1'
# df.to_excel(writer, sheet_name='O_His')

# # Save the workbook and close the Pandas Excel writer
# writer.save()

# # Read CSV file into a pandas DataFrame
# input_path = os.path.join(os.getcwd(), 'demo/evsfr/source/ieee39_ev_s_out.csv')
# df = pd.read_csv(input_path)

# # Create a Pandas Excel writer using xlsxwriter as the engine
# out_path = os.path.join(os.getcwd(), 'demo/evsfr/out/ieee39_ev_s.xlsx')
# writer = pd.ExcelWriter(out_path, engine='xlsxwriter')

# # Write DataFrame to a sheet named 'Sheet1'
# df.to_excel(writer, sheet_name='O_His')

# # Save the workbook and close the Pandas Excel writer
# writer.save()
