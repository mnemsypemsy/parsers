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
max_stack = 4      # Maximum number of stacked words

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

# Step 3: Refine grouping with x proximity and limit to max_stack elements
final_grouped_output = []

for row_index, row in enumerate(rows):
    row = sorted(row, key=lambda x: x['x0'])  # Sort by x0 within the row
    current_group = []
    current_x = None

    for element in row:
        # If within the same group (x proximity)
        if current_x is None or abs(element['x0'] - current_x) <= x_threshold:
            current_group.append({
                "text": element["text"],
                "x0": element["x0"],
                "y0": element["y0"],
                "x1": element["x1"],
                "y1": element["y1"]
            })
        else:
            # Sort current group by y (descending) and limit to max_stack
            current_group = sorted(current_group, key=lambda e: e["y0"], reverse=True)[:max_stack]
            final_grouped_output.append({
                "tag": f"sq{row_index + 1}_{len(final_grouped_output) + 1}",
                "elements": current_group
            })
            current_group = [{
                "text": element["text"],
                "x0": element["x0"],
                "y0": element["y0"],
                "x1": element["x1"],
                "y1": element["y1"]
            }]
        current_x = element["x0"]

    # Handle the last group in the row
    if current_group:
        current_group = sorted(current_group, key=lambda e: e["y0"], reverse=True)[:max_stack]
        final_grouped_output.append({
            "tag": f"sq{row_index + 1}_{len(final_grouped_output) + 1}",
            "elements": current_group
        })

# Save final grouped output to JSON
final_grouped_json_path = '/mnt/data/SA011_EOS_final_grouped_detailed_coords.json'
with open(final_grouped_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(final_grouped_output, json_file, ensure_ascii=False, indent=2)

print(f"Final grouped JSON saved to: {final_grouped_json_path}")
