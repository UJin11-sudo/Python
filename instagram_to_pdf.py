"""
Instagram Posts to PDF Converter - WITH CLEAN EXIT
Automatically cleans up all temporary files, caches, and optionally installed packages
"""

import subprocess
import sys
import os
import atexit
import shutil
import tempfile

# Global variables for cleanup
INSTALLED_PACKAGES = []
TEMP_DIRS = []
ORIGINAL_DIR = os.getcwd()

def cleanup_on_exit():
    """Clean up everything when script exits"""
    print("\n🧹 Cleaning up...")
    
    # 1. Clean temporary directories
    for temp_dir in TEMP_DIRS:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"  ✓ Removed temp directory: {temp_dir}")
        except:
            pass
    
    # 2. Clean Python cache files
    cache_dirs = ['__pycache__', '.pytest_cache', '.mypy_cache']
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name in cache_dirs:
                try:
                    shutil.rmtree(os.path.join(root, dir_name))
                    print(f"  ✓ Removed cache: {dir_name}")
                except:
                    pass
    
    # 3. Clean pip cache
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "cache", "purge"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("  ✓ Cleared pip cache")
    except:
        pass
    
    # 4. Ask about uninstalling packages
    if INSTALLED_PACKAGES:
        print("\n📦 Installed packages during this session:")
        for pkg in INSTALLED_PACKAGES:
            print(f"  - {pkg}")
        
        response = input("\n❓ Do you want to uninstall these packages? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            for pkg in INSTALLED_PACKAGES:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", pkg],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                    print(f"  ✓ Uninstalled: {pkg}")
                except:
                    print(f"  ✗ Failed to uninstall: {pkg}")
        else:
            print("  ℹ️  Packages kept installed")
    
    # 5. Return to original directory
    try:
        os.chdir(ORIGINAL_DIR)
    except:
        pass
    
    print("\n✨ Cleanup complete!")
    print("📄 Your PDF files are saved in the current directory")

# Register cleanup function to run on exit
atexit.register(cleanup_on_exit)

# Install dependencies
def install_packages():
    """Install required packages and track them for cleanup"""
    global INSTALLED_PACKAGES
    
    packages = ['requests', 'Pillow', 'reportlab', 'beautifulsoup4']
    newly_installed = []
    
    print("📦 Checking required packages...")
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package} already installed")
        except ImportError:
            print(f"  ⏳ Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "--quiet", package
                ])
                print(f"  ✓ {package} installed")
                newly_installed.append(package)
            except Exception as e:
                print(f"  ✗ Failed to install {package}: {e}")
                sys.exit(1)
    
    INSTALLED_PACKAGES = newly_installed
    
    if newly_installed:
        print(f"\n📦 {len(newly_installed)} new package(s) installed (will be cleaned up on exit)")
    else:
        print("✅ All packages already available")
    print()

# Run installation
install_packages()

# Now import all modules
import requests
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Spacer, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import json
import urllib.parse

class InstagramDownloader:
    def __init__(self):
        # Create temp directory and track it
        self.temp_dir = tempfile.mkdtemp(prefix="instagram_pdf_")
        TEMP_DIRS.append(self.temp_dir)
        
        self.images = []
        self.post_data = []
        self.output_pdf = "instagram_posts.pdf"
        
        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def extract_post_id(self, url):
        """Extract post ID from Instagram URL"""
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_media_from_instagram(self, url):
        """Get media URLs using multiple methods"""
        post_id = self.extract_post_id(url)
        if not post_id:
            return []

        media_urls = []
        print(f"📸 Fetching post: {post_id}")

        # METHOD 1: oEmbed API
        try:
            oembed_url = f"https://api.instagram.com/oembed?url={url}"
            response = self.session.get(oembed_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'thumbnail_url' in data:
                    media_urls.append(data['thumbnail_url'])
                    print("  ✓ Found image via oEmbed")
        except:
            pass

        # METHOD 2: Embed iframe
        if not media_urls:
            try:
                embed_url = f"https://www.instagram.com/p/{post_id}/embed/"
                response = self.session.get(embed_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    images = soup.find_all('img')
                    for img in images:
                        src = img.get('src')
                        if src and 'cdninstagram.com' in src:
                            if '?' in src:
                                src = src.split('?')[0]
                            if src not in media_urls:
                                media_urls.append(src)
                    if media_urls:
                        print(f"  ✓ Found {len(media_urls)} images via embed")
            except:
                pass

        # METHOD 3: GraphQL from page
        if not media_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # Look for JSON data
                    patterns = [
                        r'window\._sharedData\s*=\s*({.*?});',
                        r'"graphql":({.*?})}'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, response.text, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(1))
                                if 'entry_data' in data:
                                    entries = data['entry_data'].get('PostPage', [])
                                    for entry in entries:
                                        if 'graphql' in entry and 'shortcode_media' in entry['graphql']:
                                            media = entry['graphql']['shortcode_media']
                                            if media.get('__typename') in ['GraphImage', 'GraphVideo']:
                                                if 'display_url' in media:
                                                    media_urls.append(media['display_url'])
                                            elif media.get('__typename') == 'GraphSidecar':
                                                for node in media.get('edge_sidecar_to_children', {}).get('edges', []):
                                                    child = node.get('node', {})
                                                    if 'display_url' in child:
                                                        media_urls.append(child['display_url'])
                                
                                if media_urls:
                                    print(f"  ✓ Found {len(media_urls)} images via GraphQL")
                                    break
                            except:
                                continue
            except:
                pass

        # METHOD 4: Open Graph
        if not media_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        media_urls.append(og_image['content'])
                        print("  ✓ Found image via Open Graph")
            except:
                pass

        # Remove duplicates
        seen = set()
        unique_urls = []
        for url in media_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls

    def download_image(self, url, filename):
        """Download image with proper headers"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.instagram.com/',
            }
            response = self.session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.temp_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return filepath
            return None
        except:
            return None

    def process_post(self, url):
        """Process a single post"""
        print(f"\n📱 Processing: {url}")
        
        media_urls = self.get_media_from_instagram(url)
        
        if not media_urls:
            print(f"❌ Could not find images for this post")
            return False
        
        print(f"📸 Found {len(media_urls)} image(s)")
        
        downloaded = 0
        for i, media_url in enumerate(media_urls):
            filename = f"post_{len(self.post_data)}_{i}.jpg"
            filepath = self.download_image(media_url, filename)
            if filepath:
                self.images.append(filepath)
                downloaded += 1
                print(f"  ✓ Downloaded {i+1}/{len(media_urls)}")
            else:
                print(f"  ✗ Failed {i+1}/{len(media_urls)}")
            time.sleep(0.5)
        
        if downloaded > 0:
            self.post_data.append({
                'url': url,
                'images': downloaded,
                'total': len(media_urls)
            })
            return True
        return False

    def create_pdf(self, output_filename=None):
        """Create PDF from images"""
        if not self.images:
            print("❌ No images to create PDF")
            return None
        
        if output_filename:
            self.output_pdf = output_filename
        
        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=A4,
            title="Instagram Posts"
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title page
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Instagram Posts", title_style))
        story.append(Spacer(1, 12))
        
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor='gray'
        )
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_style))
        story.append(Spacer(1, 20))
        
        count_style = ParagraphStyle(
            'CountStyle',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            textColor='gray'
        )
        story.append(Paragraph(f"Total: {len(self.post_data)} posts, {len(self.images)} images", count_style))
        story.append(Spacer(1, 20))
        
        # Add images
        page_width, page_height = A4
        margin = 15 * mm
        available_width = page_width - (2 * margin)
        available_height = page_height - (2 * margin)
        
        image_counter = 0
        
        for post_idx, post_info in enumerate(self.post_data):
            # Post header
            post_style = ParagraphStyle(
                'PostStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10,
                alignment=TA_CENTER,
                textColor='darkblue'
            )
            story.append(Paragraph(f"📸 Post {post_idx + 1}", post_style))
            
            url_style = ParagraphStyle(
                'URLStyle',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor='gray'
            )
            story.append(Paragraph(f"{post_info['url'][:60]}...", url_style))
            story.append(Spacer(1, 10))
            
            for img_idx in range(post_info['images']):
                if image_counter >= len(self.images):
                    break
                    
                image_path = self.images[image_counter]
                image_counter += 1
                
                try:
                    if not os.path.exists(image_path):
                        continue
                        
                    with Image.open(image_path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        img_width, img_height = img.size
                        width_scale = available_width / img_width
                        height_scale = available_height / img_height
                        scale = min(width_scale, height_scale, 0.85)
                        
                        final_width = img_width * scale
                        final_height = img_height * scale
                        
                        temp_image = os.path.join(self.temp_dir, f"resized_{image_counter}.jpg")
                        img.resize((int(final_width), int(final_height)), Image.Resampling.LANCZOS).save(temp_image, 'JPEG', quality=95)
                        
                        if post_info['images'] > 1:
                            caption_style = ParagraphStyle(
                                'ImageCaption',
                                parent=styles['Normal'],
                                fontSize=9,
                                alignment=TA_CENTER,
                                textColor='gray'
                            )
                            story.append(Paragraph(f"Image {img_idx + 1}/{post_info['images']}", caption_style))
                            story.append(Spacer(1, 5))
                        
                        story.append(RLImage(temp_image, width=final_width, height=final_height))
                        story.append(Spacer(1, 12))
                        
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                    continue
            
            if post_idx < len(self.post_data) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        print(f"\n✅ PDF created: {self.output_pdf}")
        return self.output_pdf

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass

    def run(self, urls, output_pdf="instagram_posts.pdf"):
        """Main run method"""
        self.output_pdf = output_pdf
        
        print("\n" + "=" * 60)
        print("📸 INSTAGRAM TO PDF CONVERTER")
        print("=" * 60)
        print("\n⚠️  Works with PUBLIC posts only")
        print("💡 Press Ctrl+C at any time to exit and clean up\n")
        
        print(f"📋 Processing {len(urls)} post(s)...\n")
        
        success_count = 0
        for idx, url in enumerate(urls, 1):
            print(f"\n🔄 [{idx}/{len(urls)}]")
            if self.process_post(url):
                success_count += 1
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print(f"📊 Success: {success_count}/{len(urls)} posts")
        print(f"🖼️  Images: {len(self.images)}")
        print("=" * 60)
        
        if self.images:
            pdf_path = self.create_pdf(output_pdf)
            print(f"\n✨ SUCCESS! PDF: {pdf_path}")
            print(f"📁 Location: {os.path.abspath(pdf_path)}")
            return pdf_path
        else:
            print("\n❌ No images downloaded")
            return None

def main():
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM POSTS TO PDF CONVERTER")
    print("=" * 60)
    print("\n📝 Paste Instagram URLs (one per line)")
    print("   Press ENTER twice when done")
    print("   Press Ctrl+C to exit and clean up\n")
    
    urls = []
    print("📋 Enter URLs:\n")
    
    while True:
        try:
            line = input().strip()
            if not line:
                if urls:
                    break
                continue
            urls.append(line)
        except KeyboardInterrupt:
            print("\n\n⚠️ Exit requested. Cleaning up...")
            sys.exit(0)
    
    if not urls:
        print("\n❌ No URLs provided.")
        return
    
    # Validate URLs
    valid_urls = []
    for url in urls:
        if 'instagram.com/p/' in url or 'instagram.com/reel/' in url:
            valid_urls.append(url)
        else:
            print(f"⚠️ Skipping: {url}")
    
    if not valid_urls:
        print("\n❌ No valid Instagram URLs.")
        return
    
    # Output filename
    default_name = f"instagram_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    output_name = input(f"\n📄 PDF name (default: {default_name}): ").strip()
    if not output_name:
        output_name = default_name
    if not output_name.endswith('.pdf'):
        output_name += '.pdf'
    
    # Run converter
    converter = InstagramDownloader()
    try:
        converter.run(valid_urls, output_name)
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled. Cleaning up...")
        converter.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        converter.cleanup()
    finally:
        # The atexit handler will run automatically
        pass

if __name__ == "__main__":
    main()