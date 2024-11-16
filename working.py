# Import necessary libraries
import json  # For saving and handling JSON data
import pandas as pd  # For data manipulation and sorting
from pdfminer.high_level import extract_pages  # For PDF text extraction
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal  # For working with PDF elements
import fitz  # PyMuPDF, for working with PDFs and SVG conversion

# Function to extract text and its coordinates from a PDF
def extract_text_with_coordinates(pdf_path):
    """
    Extracts text along with its bounding box coordinates from a PDF.
    
    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list: A list of dictionaries, each containing text and its bounding box coordinates (x0, y0, x1, y1).
    """
    extracted_data = []  # List to store extracted text and coordinates
    for page_layout in extract_pages(pdf_path):  # Iterate through pages in the PDF
        for element in page_layout:  # Iterate through elements in the page
            if isinstance(element, LTTextBoxHorizontal):  # Check if element is a text box
                for line in element:  # Iterate through lines of text
                    if isinstance(line, LTTextLineHorizontal):  # Check if element is a text line
                        text = line.get_text().strip()  # Get text and remove extra spaces
                        if text:  # Only process non-empty text
                            bbox = line.bbox  # Get bounding box coordinates (x0, y0, x1, y1)
                            extracted_data.append({
                                "text": text,
                                "x0": bbox[0],
                                "y0": bbox[1],
                                "x1": bbox[2],
                                "y1": bbox[3]
                            })  # Append text and coordinates as a dictionary
    return extracted_data


# Function to convert PDF pages to SVG
def convert_pdf_to_svg(pdf_path, output_folder):
    """
    Converts each page of a PDF into an SVG file.
    
    Args:
        pdf_path (str): Path to the PDF file.
        output_folder (str): Directory where SVG files will be saved.

    Returns:
        list: A list of paths to the generated SVG files.
    """
    doc = fitz.open(pdf_path)  # Open the PDF document
    svg_paths = []  # List to store paths to SVG files

    for page_num in range(len(doc)):  # Loop through each page in the PDF
        svg_path = f"{output_folder}/page_{page_num + 1}.svg"  # Define SVG file path
        page = doc[page_num]  # Get the current page
        svg = page.get_svg_image()  # Convert page to SVG
        with open(svg_path, 'w', encoding='utf-8') as svg_file:
            svg_file.write(svg)  # Save SVG content to file
        svg_paths.append(svg_path)  # Append the SVG file path to the list

    doc.close()  # Close the PDF document
    return svg_paths


# Function to group text elements based on proximity
def group_text_elements_by_proximity(data, x_threshold, y_threshold):
    """
    Groups text elements based on proximity in x and y directions. Limits groups to 4 words per stack.
    
    Args:
        data (list): List of dictionaries with text and bounding box coordinates.
        x_threshold (float): Threshold for grouping by horizontal proximity.
        y_threshold (float): Threshold for grouping by vertical proximity.

    Returns:
        list: A list of grouped text elements, with tags for identification.
    """
    df = pd.DataFrame(data)  # Convert data to a DataFrame for sorting
    df_sorted = df.sort_values(by=['y0', 'x0'], ascending=[False, True])  # Sort by y (descending) and x (ascending)

    rows = []  # List to store grouped rows
    current_row = []  # Temporary storage for current row elements
    current_y = None  # Track y-coordinate for grouping

    for _, row in df_sorted.iterrows():  # Iterate through sorted data
        if current_y is None or abs(row['y0'] - current_y) <= y_threshold:  # Check vertical proximity
            current_row.append(row)  # Add to current row
        else:
            rows.append(current_row)  # Save the current row
            current_row = [row]  # Start a new row
        current_y = row['y0']  # Update current y-coordinate
    if current_row:  # Add the last row if exists
        rows.append(current_row)

    grouped_output = []  # Final grouped output
    for row_index, row in enumerate(rows):
        row = sorted(row, key=lambda x: x['x0'])  # Sort elements in the row by x-coordinate
        current_group = []  # Temporary storage for current group
        current_x = None  # Track x-coordinate for grouping

        for element in row:
            if current_x is None or abs(element['x0'] - current_x) <= x_threshold:  # Check horizontal proximity
                current_group.append({
                    "text": element["text"],
                    "x0": element["x0"],
                    "y0": element["y0"],
                    "x1": element["x1"],
                    "y1": element["y1"]
                })  # Add to the current group
            else:
                current_group = sorted(current_group, key=lambda e: e["y0"], reverse=True)[:4]  # Limit group size
                grouped_output.append({
                    "tag": f"sq{row_index + 1}_{len(grouped_output) + 1}",
                    "elements": current_group
                })  # Save the current group with a tag
                current_group = [{
                    "text": element["text"],
                    "x0": element["x0"],
                    "y0": element["y0"],
                    "x1": element["x1"],
                    "y1": element["y1"]
                }]  # Start a new group
            current_x = element["x0"]  # Update current x-coordinate

        if current_group:  # Save the last group in the row
            current_group = sorted(current_group, key=lambda e: e["y0"], reverse=True)[:4]
            grouped_output.append({
                "tag": f"sq{row_index + 1}_{len(grouped_output) + 1}",
                "elements": current_group
            })

    return grouped_output


# Main script to process the PDF and save data

# Extract text along with coordinates
text_data = extract_text_with_coordinates(pdf_path)

# Save the ungrouped text data to a JSON file
with open(detailed_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(text_data, json_file, ensure_ascii=False, indent=2)

# Group text elements by proximity and save refined data
final_grouped_data = group_text_elements_by_proximity(text_data, x_threshold, y_threshold)
with open(final_grouped_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(final_grouped_data, json_file, ensure_ascii=False, indent=2)

# Convert PDF pages to SVG and save
svg_paths = convert_pdf_to_svg(pdf_path, svg_output_folder)

# Output confirmation of saved paths
{
    "detailed_text_data_path": detailed_json_path,
    "final_grouped_data_path": final_grouped_json_path,
    "svg_paths": svg_paths
}
