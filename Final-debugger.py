import os
import subprocess
import re
import shutil

# Define paths and folders
windbg_path = r"<Your Path>Windows Kits\10\Debuggers\x64\windbg.exe"
dump_folder = r"<Your Path>\CrashDumps"
output_path = r"<Your Path>\Report"
analysis_file = r"analysis.txt"
error_names = ['StackOverflow', 'PointerRelated', 'UseAfterFree', 'BufferOverflow']

# Create the output folder if it doesn't exist
os.makedirs(output_path, exist_ok=True)

# Function to create a folder name without special characters
def clean_folder_name(name):
    return re.sub(r'[()\' ]', '', name)

def get_exception_type(content):
    if 'ExceptionCode: c00000fd (Stack overflow)' in content:
        return 'StackOverflow'
    elif 'Attempt to read from address' in content:  # Replace with your observed Address
        return 'UseAfterFree'
    elif 'Attempt to write to address 00761023' in content:  # Replace with your observed Address
        return 'PointerRelated'
    elif 'Attempt to write to address' in content:
        return 'BufferOverflow'
    else:
        return None

# Process dump files and generate output files in the corresponding folders
for dump_file in os.listdir(dump_folder):
    if dump_file.endswith('.dmp'):
        dump_file_path = os.path.join(dump_folder, dump_file)

        # Generate the output file path with the exception name
        output_file = os.path.splitext(dump_file)[0] + '_analysis.txt'
        output_file_path = os.path.join(output_path, output_file)

        cmd = [
            windbg_path,
            '-z', dump_file_path,
            '-c', '.ecxr;.exr -1;q',
            '-logo', output_file_path  
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Analysis for {dump_file} saved as {output_file}")

            # Read the content of the analysis file
            with open(output_file_path, 'r') as file:
                content = file.read()
            
            # Get the exception type from the content
            exception_type = get_exception_type(content)
            print(exception_type)

            # Update the folder name based on the exception type
            if exception_type:
                folder_name = clean_folder_name(exception_type)
            else:
                folder_name = "Unknown"

            # Move the output file to the corresponding folder
            destination_folder = os.path.join(output_path, folder_name)
            os.makedirs(destination_folder, exist_ok=True)
            new_file_path = os.path.join(destination_folder, output_file)
            shutil.move(output_file_path, new_file_path)

        except subprocess.CalledProcessError as e:
            print(f"Error analyzing {dump_file}: {e}")

# Concatenate analysis information into the analysis.txt file
analysis_file_path = os.path.join(output_path, analysis_file)
with open(analysis_file_path, "w") as analysis_file:
    for root, folders, _ in os.walk(output_path):
        for folder in folders:
            analysis_file.write(f"'{folder}':\n\n")
            folder_path = os.path.join(output_path, folder)
            for _, _, files in os.walk(folder_path):
                for file_name in files:
                    if file_name.endswith('_analysis.txt'):
                        dmp_file_name = file_name.replace('_analysis.txt', '.dmp')
                        analysis_file.write(f"File: {os.path.join(dump_folder, dmp_file_name)}\n")
            analysis_file.write("\n\n")

print(f"\nAnalysis completed. Results saved in {output_file_path}")
