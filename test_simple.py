"""
Test file that checks for null bytes in Python files
"""
import os
import sys

def check_file_for_null_bytes(file_path):
    """Check if a file contains null bytes"""
    with open(file_path, 'rb') as f:
        content = f.read()
        if b'\x00' in content:
            return True
    return False

def main():
    print("Checking for null bytes in Python files...")
    
    # Get all Python files in the getcity package
    python_files = []
    for root, dirs, files in os.walk('getcity'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Check each file for null bytes
    files_with_null_bytes = []
    for file_path in python_files:
        if check_file_for_null_bytes(file_path):
            files_with_null_bytes.append(file_path)
            print(f"Found null bytes in: {file_path}")
    
    if not files_with_null_bytes:
        print("No null bytes found in any Python files.")
        print("\nTrying to import getcity...")
        try:
            import getcity
            print("Successfully imported getcity!")
            print(f"Version: {getcity.__version__}")
            
            # Test functionality
            print("\nTesting functionality:")
            result = getcity.get_nearest_city(40.7128, -74.0060)
            print(f"Nearest city to NYC coordinates: {result}")
            
        except Exception as e:
            print(f"Error importing getcity: {e}")
    else:
        print(f"\nFound {len(files_with_null_bytes)} files with null bytes.")
        print("Please fix these files by recreating them without null bytes.")

if __name__ == "__main__":
    main() 