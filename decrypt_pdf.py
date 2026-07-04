import os
import pikepdf
from PyPDF2 import PdfReader, PdfWriter
import traceback

def decrypt_with_pikepdf(input_path, output_path, password):
    """
    Try decryption with pikepdf (supports more encryption types)
    """
    try:
        with pikepdf.open(input_path, password=password) as pdf:
            pdf.save(output_path)
        return True, "Successfully decrypted with pikepdf"
    except Exception as e:
        return False, f"pikepdf failed: {str(e)}"

def decrypt_with_pypdf2(input_path, output_path, password):
    """
    Try decryption with PyPDF2
    """
    try:
        with open(input_path, 'rb') as input_file:
            reader = PdfReader(input_file)
            
            if reader.is_encrypted:
                if reader.decrypt(password):
                    writer = PdfWriter()
                    
                    # Copy all pages
                    for page in reader.pages:
                        writer.add_page(page)
                    
                    # Copy metadata
                    if reader.metadata:
                        writer.add_metadata(reader.metadata)
                    
                    # Save decrypted file
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    return True, "Successfully decrypted with PyPDF2"
                else:
                    return False, "PyPDF2: Wrong password or unsupported encryption"
            else:
                return False, "File is not encrypted"
                
    except Exception as e:
        return False, f"PyPDF2 error: {str(e)}"

def robust_decrypt(input_path, output_path, password):
    """
    Try multiple methods to decrypt PDF
    """
    print(f"Attempting to decrypt: {os.path.basename(input_path)}")
    
    # Method 1: Try PyPDF2 first
    success, message = decrypt_with_pypdf2(input_path, output_path, password)
    if success:
        return True, message
    
    print(f"  PyPDF2 failed: {message}")
    
    # Method 2: Try pikepdf (install: pip install pikepdf)
    try:
        success, message = decrypt_with_pikepdf(input_path, output_path, password)
        if success:
            return True, message
        print(f"  pikepdf failed: {message}")
    except ImportError:
        print("  pikepdf not installed, skipping...")
    
    return False, "All decryption methods failed"

# Install required library first:
# pip install pikepdf

def main():
    """
    Main decryption function with better error handling
    """
    input_folder = r""
    output_folder = r""
    password = ""
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Get PDF files
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found!")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for filename in pdf_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        success, message = robust_decrypt(input_path, output_path, password)
        
        if success:
            print(f"  ✅ SUCCESS: {message}")
            successful += 1
        else:
            print(f"  ❌ FAILED: {message}")
            failed += 1
        
        print("-" * 40)
    
    print("DECRYPTION SUMMARY:")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()