import pandas as pd
from io import BytesIO

def to_excel(df):
    """
    Chuyển đổi một DataFrame thành file Excel trong bộ nhớ (bytes).
    """
    output = BytesIO()
    # Sử dụng 'with' để đảm bảo writer được đóng đúng cách
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='FilteredData')
    # Lấy giá trị từ buffer sau khi writer đã đóng
    processed_data = output.getvalue()
    return processed_data
