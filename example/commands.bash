# Generate md
python ../AIaaLT.py   --function "lambda args: round(args[0] * 0.225 + args[1] * 0.02 - 2, 1)"   --ranges "height:160:190:2:cm" "weight:50:100:5:kg"   --title "EU Shoe Size Prediction"   --notes "Linear regression: shoe_size = 0.225×height + 0.02×weight - 2

Based on biomechanical observation that foot length is around 15% of height."   --output-dir "shoe_size_prediction"

# Convert md to pdf
../tables_to_pdf.sh shoe_size_prediction/ shoe.pdf

