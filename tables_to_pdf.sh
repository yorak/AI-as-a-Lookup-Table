#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: $0 <input_directory> <output_pdf_file>"
    echo ""
    echo "Convert markdown files to a single PDF document"
    echo ""
    echo "Arguments:"
    echo "  input_directory   Directory containing .md files"
    echo "  output_pdf_file   Output PDF filename (e.g., tables.pdf)"
    echo ""
    echo "Examples:"
    echo "  $0 hartia_B_tables output.pdf"
    echo "  $0 ./my_tables report.pdf"
    echo ""
    echo "Requirements:"
    echo "  - pandoc (for PDF conversion)"
    echo "  - xelatex (LaTeX engine)"
    echo ""
    echo "Install requirements:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex"
    echo "  macOS:         brew install pandoc mactex"
    echo "  Fedora:        sudo dnf install pandoc texlive-xetex"
}

# Check for help flags
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

# Validate arguments
if [ $# -ne 2 ]; then
    echo "Error: Exactly 2 arguments required"
    echo ""
    show_usage
    exit 1
fi

input_dir="$1"
output_pdf="$2"

# Validate input directory
if [ ! -d "$input_dir" ]; then
    echo "Error: Input directory '$input_dir' does not exist"
    exit 1
fi

# Check if directory contains any .md files
md_count=$(find "$input_dir" -name "*.md" -type f | wc -l)
if [ "$md_count" -eq 0 ]; then
    echo "Error: No .md files found in '$input_dir'"
    exit 1
fi

# Validate output directory exists
output_dir=$(dirname "$output_pdf")
if [ ! -d "$output_dir" ]; then
    echo "Error: Output directory '$output_dir' does not exist"
    exit 1
fi

# Check for required tools
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc not found. Please install pandoc to generate PDFs."
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex"
    echo "  macOS:         brew install pandoc mactex"
    echo "  Fedora:        sudo dnf install pandoc texlive-xetex"
    exit 1
fi

echo "Generating PDF from markdown files..."
echo "Processing: $input_dir -> $output_pdf"
echo "Found $md_count markdown files"

# Create a temporary file for the concatenated markdown
temp_file=$(mktemp) || {
    echo "Error: Could not create temporary file"
    exit 1
}

# Trap to ensure cleanup on script exit
trap 'rm -f "$temp_file"' EXIT

# Find all markdown files, sort them naturally and concatenate them
file_count=0
for file in $(find "$input_dir" -name "*.md" -type f | sort -V); do
    file_count=$((file_count + 1))
    
    # Extract identifier from filename for logging (more generic than just weight)
    filename=$(basename "$file" .md)
    echo "  [$file_count/$md_count] Adding: $filename"
    
    # Append file content
    cat "$file" >> "$temp_file" || {
        echo "Error: Could not read file '$file'"
        exit 1
    }
    
    # Add page break between files (but not after the last one)
    if [ $file_count -lt $md_count ]; then
        echo -e "\n\\pagebreak\n" >> "$temp_file"
    fi
done

# Convert to PDF using pandoc
echo "  Converting to PDF with pandoc..."
pandoc "$temp_file" \
    -o "$output_pdf" \
    --pdf-engine=xelatex \
    -V geometry:margin=1in \
    -V papersize=a4 \
    -V geometry:landscape

if [ $? -eq 0 ]; then
    file_size=$(ls -lh "$output_pdf" | awk '{print $5}')
    echo "  ✓ Successfully generated $output_pdf ($file_size)"
else
    echo "  ✗ Error: pandoc conversion failed"
    exit 1
fi

echo "Done! Processed $file_count files into PDF."