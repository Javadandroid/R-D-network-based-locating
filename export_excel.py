import pandas as pd
import sys
import os

# تنظیمات
INPUT_FILE = 'openCellIdIranDatabase.csv.gz'  # یا نام فایل اصلی بزرگ: 'MLS-full-cell-export-final.csv.gz'
OUTPUT_FILE = 'open_cell_id_iran_db.csv'
TARGET_MCC = 432  # کد ایران

# نام ستون‌های استاندارد موزیلا
COLUMNS = [
    'radio', 'mcc', 'mnc', 'lac', 'cid', 'psc',
    'lon', 'lat', 'range', 'samples', 'changeable',
    'created', 'updated', 'avgSignal'
]

def main():
    print(f"Reading from {INPUT_FILE}...")
    
    # لیست برای ذخیره تکه‌های پیدا شده
    iran_data_chunks = []
    
    try:
        # فایل را به صورت تکه‌های ۱۰۰ هزار تایی می‌خوانیم تا رم پر نشود
        # compression='gzip' باعث می‌شود فایل فشرده را مستقیم بخواند
        chunk_iterator = pd.read_csv(
            INPUT_FILE, 
            names=COLUMNS, 
            chunksize=100000, 
            compression='gzip',
            header=None,  # فایل اصلی معمولا هدر ندارد
            low_memory=False
        )

        total_rows = 0
        
        for i, chunk in enumerate(chunk_iterator):
            # فیلتر کردن فقط ایران (MCC = 432)
            iran_subset = chunk[chunk['mcc'] == TARGET_MCC]
            
            if not iran_subset.empty:
                iran_data_chunks.append(iran_subset)
                total_rows += len(iran_subset)
                
            # نمایش پیشرفت کار
            sys.stdout.write(f"\rProcessed chunk {i+1} - Found {total_rows} cells so far...")
            sys.stdout.flush()

        print(f"\n\nProcessing finished. Total cells found: {total_rows}")
        
        if total_rows == 0:
            print("No data found for MCC 432!")
            return

        print("Combining data...")
        final_df = pd.concat(iran_data_chunks)

        print(f"Saving to Excel ({OUTPUT_FILE})... This may take a minute.")
        # ذخیره بدون ایندکس (شماره ردیف اضافه)
        # final_df.to_excel(OUTPUT_FILE, index=False)
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print("Done! ✅")
        print(f"File saved at: {os.path.abspath(OUTPUT_FILE)}")

    except FileNotFoundError:
        print(f"Error: File '{INPUT_FILE}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()