import os
import pandas as pd

# Read CSV file into a pandas DataFrame
input_path = os.path.join(os.getcwd(), 'demo/evsfr/source/ieee39_ev_f_out.csv')
df = pd.read_csv(input_path)

# Create a Pandas Excel writer using xlsxwriter as the engine
out_path = os.path.join(os.getcwd(), 'demo/evsfr/out/ieee39_ev_f.xlsx')
writer = pd.ExcelWriter(out_path, engine='xlsxwriter')

# Write DataFrame to a sheet named 'Sheet1'
df.to_excel(writer, sheet_name='O_His')

# Save the workbook and close the Pandas Excel writer
writer.save()

# Read CSV file into a pandas DataFrame
input_path = os.path.join(os.getcwd(), 'demo/evsfr/source/ieee39_ev_fict_out.csv')
df = pd.read_csv(input_path)

# Create a Pandas Excel writer using xlsxwriter as the engine
out_path = os.path.join(os.getcwd(), 'demo/evsfr/out/ieee39_ev_fict.xlsx')
writer = pd.ExcelWriter(out_path, engine='xlsxwriter')

# Write DataFrame to a sheet named 'Sheet1'
df.to_excel(writer, sheet_name='O_His')

# Save the workbook and close the Pandas Excel writer
writer.save()

# Read CSV file into a pandas DataFrame
input_path = os.path.join(os.getcwd(), 'demo/evsfr/source/ieee39_ev_s_out.csv')
df = pd.read_csv(input_path)

# Create a Pandas Excel writer using xlsxwriter as the engine
out_path = os.path.join(os.getcwd(), 'demo/evsfr/out/ieee39_ev_s.xlsx')
writer = pd.ExcelWriter(out_path, engine='xlsxwriter')

# Write DataFrame to a sheet named 'Sheet1'
df.to_excel(writer, sheet_name='O_His')

# Save the workbook and close the Pandas Excel writer
writer.save()
