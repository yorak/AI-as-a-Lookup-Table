#!/usr/bin/env python3
"""
AI or Machine Learning (ML) function to Lookup Table Generator

Generates markdown tables from mathematical functions with 2-3 input variables.
Supports both Python functions and Dart function parsing.
"""

import os
import re
import argparse
import sys
from typing import Callable, List, Tuple, Optional


def parse_dart_function(file_path: str) -> str:
    """Parse a Dart function file and convert to Python lambda."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Extract the function body
        body_start = content.find('{')
        body_end = content.rfind('}')
        
        if body_start == -1 or body_end == -1:
            raise ValueError(f"Could not find function body in {file_path}")
        
        function_body = content[body_start+1:body_end].strip()
        
        # Extract the return statement
        lines = function_body.split('\n')
        return_line = None
        
        for line in lines:
            if 'return' in line:
                return_line = line.strip()
                break
        
        if not return_line:
            raise ValueError(f"Could not find return statement in {file_path}")
        
        # Parse the formula
        formula = return_line.replace('return', '').strip().rstrip(';')
        
        # Replace input[n] with args[n]
        formula = re.sub(r'input\[(\d+)\]', r'args[\1]', formula)
        
        return f"lambda args: {formula}"
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Dart function file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error parsing Dart function from {file_path}: {e}")


def create_function(func_input: str) -> Callable:
    """Create a function from string input (either Python code or Dart file path)."""
    func_input = func_input.strip()
    
    if func_input.endswith('.dart'):
        # Parse Dart function file
        python_function_str = parse_dart_function(func_input)
        try:
            return eval(python_function_str)
        except Exception as e:
            raise ValueError(f"Error evaluating parsed Dart function: {e}")
    else:
        # Assume it's Python code
        try:
            # Support both lambda and def function definitions
            if func_input.startswith('lambda'):
                return eval(func_input)
            elif func_input.startswith('def '):
                # Execute function definition and extract the function
                local_vars = {}
                exec(func_input, globals(), local_vars)
                # Find the function in local variables
                funcs = [v for v in local_vars.values() if callable(v)]
                if not funcs:
                    raise ValueError("No callable function found in definition")
                return funcs[0]
            else:
                # Try to eval as expression that returns a function
                return eval(func_input)
        except Exception as e:
            raise ValueError(f"Error creating function from Python code: {e}")


def parse_range_spec(range_spec: str) -> Tuple[str, range]:
    """Parse range specification like 'weight:50:155:5' -> ('weight', range(50, 155, 5))."""
    parts = range_spec.split(':')
    if len(parts) != 4:
        raise ValueError(f"Range spec must have format 'name:start:stop:step', got: {range_spec}")
    
    name = parts[0]
    try:
        start = int(parts[1])
        stop = int(parts[2])
        step = int(parts[3])
        return name, range(start, stop + step, step)  # +step to include stop value
    except ValueError as e:
        raise ValueError(f"Invalid numeric values in range spec '{range_spec}': {e}")


def load_notes(notes_input: str) -> str:
    """Load notes from string or file."""
    notes_input = notes_input.strip()
    
    if notes_input.endswith('.md'):
        try:
            with open(notes_input, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Notes file not found: {notes_input}")
    else:
        return notes_input


def generate_tables(output_dir: str, title: str, ranges_data: List[Tuple[str, range]], 
                   func: Callable, notes: str):
    """Generate markdown tables for functions with 2-3 dimensions."""
    os.makedirs(output_dir, exist_ok=True)
    
    if len(ranges_data) == 2:
        # 2D case: single table
        (row_name, row_range), (col_name, col_range) = ranges_data
        filename = f"{output_dir}/{row_name}2{col_name}.md"
        
        _write_table_file(filename, title, notes, row_name, row_range, 
                         col_name, col_range, func, None, None)
        
        print(f"Generated table file: {filename}")
        
    elif len(ranges_data) == 3:
        # 3D case: multiple tables (one per first dimension value)
        (first_name, first_range), (row_name, row_range), (col_name, col_range) = ranges_data
        
        for first_val in first_range:
            filename = f"{output_dir}/{first_name}_{first_val:03d}.md"
            table_title = f"{title}: {first_name} = {first_val}"
            
            _write_table_file(filename, table_title, notes, row_name, row_range,
                             col_name, col_range, func, first_val, first_name)
        
        print(f"Generated {len(first_range)} table files in '{output_dir}' directory")
    
    else:
        raise ValueError(f"Unsupported number of dimensions: {len(ranges_data)}")


def _write_table_file(filename: str, title: str, notes: str, row_name: str, row_range: range,
                     col_name: str, col_range: range, func: Callable, 
                     first_val: Optional[int], first_name: Optional[str]):
    """Write a single markdown table file."""
    with open(filename, 'w') as f:
        f.write(f"# {title}\n\n")
        
        if notes:
            f.write(f"{notes}\n\n")
        
        # Create table header
        f.write(f"| ↓{row_name[0]}, {col_name[0]}→ |")
        for col_val in col_range:
            f.write(f" {col_val} |")
        f.write("\n")
        
        # Create separator row
        f.write("|" + "-" * 20 + "|")
        for _ in col_range:
            f.write(" --- |")
        f.write("\n")
        
        # Create table rows
        for row_val in row_range:
            f.write(f"| {row_val} |")
            for col_val in col_range:
                try:
                    # Build arguments based on dimensionality
                    if first_val is not None:
                        # 3D case
                        args = [first_val, row_val, col_val]
                        arg_str = f"{first_name}={first_val}, {row_name}={row_val}, {col_name}={col_val}"
                    else:
                        # 2D case
                        args = [row_val, col_val]
                        arg_str = f"{row_name}={row_val}, {col_name}={col_val}"
                    
                    result = func(args)
                    f.write(f" {result} |")
                except Exception as e:
                    f.write(f" ERROR |")
                    print(f"Warning: Error calculating function({arg_str}): {e}")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown tables from mathematical functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 2D function
  python generic_table_generator.py \\
    --function "lambda args: args[0] * args[1]" \\
    --ranges "x:1:10:1" "y:1:5:1" \\
    --title "Multiplication Table" \\
    --output-dir "multiply_tables"

  # 3D function from Dart file
  python generic_table_generator.py \\
    --function "model.dart" \\
    --ranges "weight:50:150:5" "height:150:200:5" "age:20:80:10" \\
    --title "BMI Prediction" \\
    --notes "notes.md" \\
    --output-dir "bmi_tables"
        """)
    
    parser.add_argument('--function', '-f', required=True,
                       help='Function definition (Python lambda/def) or Dart file path')
    
    parser.add_argument('--ranges', '-r', nargs='+', required=True,
                       help='Input ranges in format "name:start:stop:step" (2-3 ranges)')
    
    parser.add_argument('--title', '-t', required=True,
                       help='Title for the generated tables')
    
    parser.add_argument('--output-dir', '-o', default='output_tables',
                       help='Output directory for generated tables (default: output_tables)')
    
    parser.add_argument('--notes', '-n', default='',
                       help='Explanatory notes (multiline string) or path to .md file')
    
    args = parser.parse_args()
    
    # Validate number of ranges
    if len(args.ranges) < 2 or len(args.ranges) > 3:
        parser.error("Must specify 2-3 input ranges")
    
    try:
        # Create function
        func = create_function(args.function)
        
        # Parse ranges
        ranges_data = []
        for range_spec in args.ranges:
            name, range_obj = parse_range_spec(range_spec)
            ranges_data.append((name, range_obj))
        
        # Load notes
        notes = load_notes(args.notes) if args.notes else ""
        
        # Generate tables
        generate_tables(args.output_dir, args.title, ranges_data, func, notes)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()