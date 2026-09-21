import qrcode
import os
BASE_URL="http://127.0.0.1:5000/menu?table"
NUMBER_OF_TABLES=5

os.makedirs('table_qr_codes', exist_ok=True)
for table_number in range(1, NUMBER_OF_TABLES + 1):
    url=BASE_URL + str(table_number)
    img=qrcode.make(url)
    img.save(f'table_qr_codes/table_{table_number}.png')
    print(f'Generated QR for Table {table_number} -> {url}')
print("Done! Check the 'table_qr_codes' folder.")