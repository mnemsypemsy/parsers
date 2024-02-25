<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Load the database credentials and domain map from the json file
$configs = json_decode(file_get_contents('/var/www/configs.json'));

// Function to parse the solution and generate JSON data
function parseSolutionToJSON($solution, $hints) {
    $json_data = array(
        "squares" => array(),
        "cols" => 9,
        "rows" => 9,
        "squareSize" => 60,
        "width" => 15,
        "height" => 14,
        "pointers" => array(),
        "largePointers" => array(),
        "keys" => array(),
        "ghostSquares" => array(),
        "ghostSquares2" => array(),
        "ghostSquares3" => array(),
        "ghostSquares4" => array(),
        "images" => array(
            array(
                "style" => array(
                    "width" => "1px",
                    "height" => "1px",
                    "top" => "0px",
                    "left" => "1px"
                ),
                "cx" => 0,
                "cy" => 0,
                "standard" => true,
                "url" => "dummy.jpg",
                "visible" => false
            )
        ),
        "hints" => $hints // Include hints in the JSON data
    );

    // Loop through each character in the solution
    for ($i = 0; $i < 81; $i++) {
        $x = $i % 9;
        $y = floor($i / 9);
        $chr = $solution[$i];

        $square = array(
            "style" => array(
                "top" => $y * 60 . "px",
                "left" => $x * 60 . "px"
            ),
            "position" => array(
                "x" => $x,
                "y" => $y
            ),
            "chr" => $chr,
            "isnew" => 1,
            "focusInput" => true,
            "left" => $x * 60 . "px",
            "top" => $y * 60 . "px"
        );

        $json_data["squares"][] = $square;
    }

    return json_encode($json_data);
}

// Function to parse each text file and insert JSON data into the database
function parseAndInsertFiles($file_dir, $db_connection, $simulate, $total_inserts) {
    $files = glob($file_dir . '/*.txt');

    foreach ($files as $file) {
        $content = file_get_contents($file);
        $lines = explode("\n", $content);

        // Find the start and end markers for the solution section
        $solution_start = array_search('[solution]', $lines);
        $solution_end = count($lines);


        // Extract the solution content
        $solution_lines = array_slice($lines, $solution_start + 1, $solution_end - $solution_start - 1);
        $solution = implode("", $solution_lines);


        // If there's a next section marker, adjust the end accordingly
        $next_section = array_search('[hints]', $lines);
        if ($next_section !== false && $next_section > $solution_start) {
            $solution_end = $next_section;
        }

        // Extract the hints content
        $hints_start = array_search('[hints]', $lines);
        $hints_end = array_search('[solution]', $lines);
        $hints_lines = array_slice($lines, $hints_start + 1, $hints_end - $hints_start - 1);
        $hints = implode("", $hints_lines);

        // Parse solution to JSON
        $json_data = parseSolutionToJSON($solution, $hints);

        // Data to be inserted
        $ID = NULL;
        $TITLE = pathinfo($file, PATHINFO_FILENAME);
        $BREAD = '-';
        $COLS = '9';
        $sROWS = '9';
        $WIDTH = '1';
        $HEIGHT = '1';
        $FILENAME = pathinfo($file, PATHINFO_FILENAME);
        $sTOP = '1';
        $BOTTOM = '1';
        $sLEFT = '1';
        $sRIGHT = '1';
        $COLWIDTH = '60';
        $COLHEIGHT = '60';
        $TEXTSIZE = '0';
        $WORDBREAK = '';
        $JSONDATA = $json_data;
        $LANGUAGE = '1';
        $VALID = '2024-02-29 00:00:00';
        $LASTCHANGE = '2024-02-15 13:39:17';
        $OWNER = '5568273154';
        $PUBLISHED = '1';
        $COMPETITIONVALID = '2024-02-29';
        $NOTES = '-';
        $LABEL = '';
        $SHOWSAVE = '1';
        $OPENCOMPETE = '1';
        $SUDOKO = '100';
        $INSTRUCTIONS = '';
        $CONTESTVALID = '2024-02-29';
        $URLHASH = substr(md5(uniqid($ID, true)), 0, 32);
        $FOLDER = '90';
        $HELP = '';
        $CUSTOMCOLS = '9';
        $CUSTOMROWS = '9';
        $CONSTRUCTOR = 'AI';

        $sql = "INSERT INTO DATA (
            ID, TITLE, BREAD, COLS, sROWS, WIDTH, HEIGHT, FILENAME, 
            sTOP, BOTTOM, sLEFT, sRIGHT, COLWIDTH, COLHEIGHT, TEXTSIZE, 
            WORDBREAK, JSONDATA, LANGUAGE, VALID, LASTCHANGE, OWNER, 
            PUBLISHED, COMPETITIONVALID, NOTES, LABEL, SHOWSAVE, OPENCOMPETE, 
            SUDOKO, INSTRUCTIONS, CONTESTVALID, URLHASH, FOLDER, HELP, 
            CUSTOMCOLS, CUSTOMROWS, CONSTRUCTOR
        ) 
        VALUES (
            NULL, '$TITLE', '$BREAD', '$COLS', '$sROWS', '$WIDTH', '$HEIGHT', 
            '$FILENAME', '$sTOP', '$BOTTOM', '$sLEFT', '$sRIGHT', '$COLWIDTH', 
            '$COLHEIGHT', '$TEXTSIZE', '$WORDBREAK', '$JSONDATA', '$LANGUAGE', 
            '$VALID', '$LASTCHANGE', '$OWNER', '$PUBLISHED', '$COMPETITIONVALID', 
            '$NOTES', '$LABEL', '$SHOWSAVE', '$OPENCOMPETE', '$SUDOKO', 
            '$INSTRUCTIONS', '$CONTESTVALID', '$URLHASH', '$FOLDER', '$HELP', 
            '$CUSTOMCOLS', '$CUSTOMROWS', '$CONSTRUCTOR'
        )";

        // Execute the SQL statement
        // Assuming $conn is your database connection object
        if (!$simulate) {
            if ($db_connection->query($sql) === TRUE) {
                $total_inserts ++;
            } else {
                echo "Error: " . $sql . "<br>" . $db_connection->error;
            }
        } else {

            $total_inserts ++;
        }
    }
    return $total_inserts;
}
$total_inserts = 0;
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    if (!empty($_POST['folder'])) {
        // Create connection
        $db = "kryssv2";
        $db_connection = new mysqli($configs->host, $configs->user, $configs->pass, $db);

        // Check connection
        if ($db_connection->connect_error) {
            die("Connection failed: " . $db_connection->connect_error);
        }

        // Directory containing text files
        $file_dir = $_POST['folder'];

        // Handle simulation checkbox
        $simulate = isset($_POST['simulate']) ? true : false;

        // Parse and insert files
        $total_inserts = parseAndInsertFiles($file_dir, $db_connection, $simulate, $total_inserts);

        // Close connection
        $db_connection->close();
    } else {
        echo "Folder field cannot be empty";
    }
}

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sudoku File Parser</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }

        form {
            text-align: center;
        }

        label {
            display: block;
            margin-bottom: 10px;
            color: #666;
        }

        input[type="text"],
        input[type="checkbox"],
        button {
            width: calc(100% - 22px);
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 16px;
            box-sizing: border-box;
        }

        input[type="checkbox"] {
            width: auto;
            margin-right: 5px;
        }

        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }

        button:hover {
            background-color: #45a049;
        }

        footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sudoku File Parser</h1><br>
        <form action="<?php echo $_SERVER['PHP_SELF']; ?>" method="post">
            <label for="folder">Folder containing Sudoku files:</label>
            <input type="text" id="folder" name="folder" required>
            <br>
            <label for="simulate">
                <input type="checkbox" id="simulate" name="simulate"> Simulate
            </label>
            <br>
            <button type="submit">Parse and Insert</button>
        </form>
        <center>Total imports: <?php echo $total_inserts;?></center>
    </div>
    <footer>
        <p>&copy; Daniel Moreira</p>
    </footer>



    <br><br>
    <div class="container">
        <h1>Sudoku File Parser Documentation</h1>

        <h2>1. Introduction</h2>
        <p>Welcome to the comprehensive documentation for the Sudoku File Parser. This document provides an extensive overview of the parser, including its architecture, functionality, usage, and implementation details.</p>

        <h2>2. Sudoku File Format</h2>
        <p>The Sudoku puzzle files follow a specific format:</p>
        <pre>
9x9:
[numbers]
51......9
.3.....1.
..769....
...1.6.47
7..8..92.
1...49.3.
2..9.8..4
...53719.
379...6..
[hints]
51......9
.3.....1.
..769....
...1.6.47
7..8..92.
1...49.3.
2..9.8..4
...53719.
379...6..
[solution]
512384769
936275418
487691253
893126547
764853921
125749836
251968374
648537192
379412685
        </pre>
        <p>The Sudoku file consists of three main sections:</p>
        <ul>
            <li><strong>Numbers:</strong> Represents the initial state of the Sudoku puzzle.</li>
            <li><strong>Hints:</strong> Provides additional clues or constraints for solving the puzzle.</li>
            <li><strong>Solution:</strong> Contains the correct solution to the puzzle.</li>
        </ul>
        <p>In each section, the puzzle is represented as a grid of characters, where each character denotes a cell's value (digit) or empty space (dot).</p>

        <h2>3. Parser Functionality</h2>
        <p>The parser offers the following functionality:</p>
        <ul>
            <li><strong>Parsing:</strong> Extracts data from Sudoku puzzle text files.</li>
            <li><strong>Conversion:</strong> Converts the extracted data into a structured format (JSON).</li>
            <li><strong>Database Insertion:</strong> Inserts the parsed puzzle data into a database table for storage and manipulation.</li>
            <li><strong>Simulation:</strong> Optionally simulates the insertion process without modifying the database, useful for testing and validation.</li>
        </ul>

        <h2>4. Usage</h2>
        <p>To use the parser, follow these steps:</p>
        <ol>
            <li>Ensure that the PHP environment is set up correctly on your server.</li>
            <li>Create a folder containing text files, each representing a Sudoku puzzle.</li>
            <li>Access the parser interface through a web browser.</li>
            <li>Specify the path to the folder containing Sudoku files.</li>
            <li>Optionally, select the simulation checkbox to simulate the insertion process.</li>
            <li>Click "Parse and Insert" to initiate the parsing and insertion process.</li>
        </ol>

        <h2>5. Conclusion</h2>
        <p>The Sudoku File Parser is a valuable tool for automating the import of Sudoku puzzles into a system. By following this documentation, users can understand its architecture, functionality, and implementation details, enabling them to effectively utilize and extend its capabilities.</p>
    </div>
</body>
</html>
