import json
import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal

# Function to extract text along with coordinates from the PDF
def extract_text_with_coordinates(pdf_path):
    extracted_data = []
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                for line in element:
                    if isinstance(line, LTTextLineHorizontal):
                        text = line.get_text().strip()
                        if text:
                            bbox = line.bbox
                            extracted_data.append({
                                "text": text,
                                "x0": bbox[0],
                                "y0": bbox[1],
                                "x1": bbox[2],
                                "y1": bbox[3]
                            })
    return extracted_data

# Load the PDF and extract data
file_path = '/mnt/data/SA011 EOS.pdf'
data = extract_text_with_coordinates(file_path)

# Convert to a DataFrame
df = pd.DataFrame(data)

# Define thresholds
y_threshold = 10  # Proximity threshold for grouping rows by y-coordinate
x_threshold = 20  # Proximity threshold for grouping within a row by x-coordinate

# Step 1: Sort by y0 (descending) and then x0 (ascending)
df_sorted = df.sort_values(by=['y0', 'x0'], ascending=[False, True])

# Step 2: Group by y0 proximity into rows
rows = []
current_row = []
current_y = None

for _, row in df_sorted.iterrows():
    if current_y is None or abs(row['y0'] - current_y) <= y_threshold:
        current_row.append(row)
    else:
        rows.append(current_row)
        current_row = [row]
    current_y = row['y0']
if current_row:
    rows.append(current_row)

# Step 3: Within each row, group by x0 proximity and tag
output = []
for row_index, row in enumerate(rows):
    row = sorted(row, key=lambda x: x['x0'])  # Sort by x0 within the row
    row_output = []
    current_group = []
    current_x = None

    for element in row:
        if current_x is None or abs(element['x0'] - current_x) <= x_threshold:
            current_group.append(element['text'])
        else:
            row_output.append({
                "tag": f"sq{row_index + 1}_{len(row_output) + 1}",
                "text": " ".join(current_group)
            })
            current_group = [element['text']]
        current_x = element['x0']
    if current_group:
        row_output.append({
            "tag": f"sq{row_index + 1}_{len(row_output) + 1}",
            "text": " ".join(current_group)
        })

    output.extend(row_output)

# Save as JSON
sorted_tagged_json_path = '/mnt/data/SA011_EOS_sorted_tagged.json'
with open(sorted_tagged_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(output, json_file, ensure_ascii=False, indent=2)

# Print the output path for reference
print(f"Sorted and tagged JSON saved to: {sorted_tagged_json_path}")
