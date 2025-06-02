# convert_encoding.py

with open('invoicemgmt_backup.json', 'rb') as source_file:
    raw_data = source_file.read().decode('utf-16')  # or 'utf-8-sig' if needed

with open('invoicemgmt_backup_fixed.json', 'w', encoding='utf-8') as target_file:
    target_file.write(raw_data)

print("Encoding conversion complete. Use invoicemgmt_backup_fixed.json for loaddata.")
