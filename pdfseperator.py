import os
import shutil
import sys

try:
    from PyPDF2 import PdfReader
    print("PyPDF2 library imported successfully!")
except ImportError:
    print("ERROR: PyPDF2 is not installed. Please run: pip install pypdf2")
    sys.exit(1)

def check_pdf_encryption(pdf_path):
    """
    Check if a PDF file is encrypted
    Returns: True if encrypted, False if not encrypted
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            return reader.is_encrypted
    except Exception as e:
        print(f"  Error reading {os.path.basename(pdf_path)}: {str(e)[:50]}...")
        return True  # Treat unreadable files as encrypted

def separate_pdfs(source_folder, encrypted_folder, unencrypted_folder):
    """
    Separate PDF files into encrypted and unencrypted folders
    """
    # Create folders if they don't exist
    os.makedirs(encrypted_folder, exist_ok=True)
    os.makedirs(unencrypted_folder, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(source_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the source folder!")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    print("-" * 50)
    
    encrypted_count = 0
    unencrypted_count = 0
    
    for filename in pdf_files:
        file_path = os.path.join(source_folder, filename)
        
        print(f"Checking: {filename}")
        
        if check_pdf_encryption(file_path):
            destination = os.path.join(encrypted_folder, filename)
            print(f"  → ENCRYPTED - moving to encrypted folder")
            encrypted_count += 1
        else:
            destination = os.path.join(unencrypted_folder, filename)
            print(f"  → Not encrypted - moving to unencrypted folder")
            unencrypted_count += 1
        
        # Move the file
        shutil.move(file_path, destination)
    
    print("-" * 50)
    print("PROCESSING COMPLETE!")
    print(f"Encrypted PDFs: {encrypted_count}")
    print(f"Unencrypted PDFs: {unencrypted_count}")
    print(f"Total processed: {encrypted_count + unencrypted_count}")

def main():
    """
    Main function - configure your folders here
    """
    # CONFIGURE THESE PATHS TO MATCH YOUR SYSTEM
    source_folder = r"C:\Users\uddes\Desktop\zerodha docs\Encrypted"  # Folder with all your PDFs
    encrypted_folder = r"C:\Users\uddes\Desktop\zerodha docs\Encrypted"  # Where encrypted PDFs will go
    unencrypted_folder = r"C:\Users\uddes\Desktop\zerodha docs\Decrypted"  # Where unencrypted PDFs will go
    
    # For Mac/Linux users, use paths like:
    # source_folder = "/Users/YourName/PDFs"
    # encrypted_folder = "/Users/YourName/PDFs/Encrypted"
    # unencrypted_folder = "/Users/YourName/PDFs/Unencrypted"
    
    print("PDF Encryption Checker")
    print("=" * 50)
    
    # Verify source folder exists
    if not os.path.exists(source_folder):
        print(f"ERROR: Source folder does not exist: {source_folder}")
        print("Please update the folder paths in the script.")
        return
    
    print(f"Source folder: {source_folder}")
    print(f"Encrypted folder: {encrypted_folder}")
    print(f"Unencrypted folder: {unencrypted_folder}")
    print()
    
    # Confirm before proceeding
    response = input("Do you want to continue? (y/n): ").lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    # Run the separation process
    separate_pdfs(source_folder, encrypted_folder, unencrypted_folder)

if __name__ == "__main__":
    main()