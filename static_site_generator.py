#!/usr/bin/env python3
"""
Script to generate a static version of the Flask application for GitHub Pages.
This script:
1. Freezes the Flask application into static HTML files
2. Prepares the static site for GitHub Pages
3. Uploads the static site to GitHub using the GitHub API
"""

import os
import sys
import json
import shutil
import requests
import base64
import time
from flask_frozen import Freezer
from urllib.parse import urlparse
from app import app

GITHUB_API_URL = "https://api.github.com"
OUTPUT_DIR = "build"

def setup_freezer():
    """Configure and return a Freezer instance for the Flask app"""
    app.config['FREEZER_DESTINATION'] = OUTPUT_DIR
    app.config['FREEZER_RELATIVE_URLS'] = True
    app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
    
    # Create a freezer for the Flask app
    freezer = Freezer(app)
    
    # Define URLs that would normally be generated dynamically
    @freezer.register_generator
    def url_generator():
        # Yield URLs that need to be generated
        yield '/'  # Home page
        yield '/success'  # Success page
        yield '/admin-login'  # Admin login page
        
    return freezer

def modify_static_files():
    """Modify static files to work with GitHub Pages"""
    print("Modifying static files for GitHub Pages...")
    
    # Create a .nojekyll file to disable Jekyll processing
    with open(os.path.join(OUTPUT_DIR, '.nojekyll'), 'w') as f:
        f.write('')
    
    # Create a CNAME file if needed for custom domain
    # with open(os.path.join(OUTPUT_DIR, 'CNAME'), 'w') as f:
    #     f.write('your-custom-domain.com')
    
    # Create a minimal index.html for testing
    # This is a fallback file in case something goes wrong with the freezing process
    fallback_html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Розыгрыш MERCEDES</title>
        <meta http-equiv="refresh" content="0;url=index.html">
    </head>
    <body>
        <p>Redirecting to the main page...</p>
        <script>window.location.href = "index.html";</script>
    </body>
    </html>
    """
    
    # Only create this if not already generated
    if not os.path.exists(os.path.join(OUTPUT_DIR, 'index.html')):
        with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(fallback_html)
    
    # Copy the data directory
    data_dir = os.path.join(os.getcwd(), 'data')
    dest_data_dir = os.path.join(OUTPUT_DIR, 'data')
    if os.path.exists(data_dir):
        if not os.path.exists(dest_data_dir):
            os.makedirs(dest_data_dir)
        for file in os.listdir(data_dir):
            src_file = os.path.join(data_dir, file)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dest_data_dir)

def fix_urls_in_html():
    """Fix URLs in the generated HTML files to work with GitHub Pages"""
    print("Fixing URLs in static HTML files...")
    
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix URLs: replace Flask's url_for with relative paths
                # This is a simple, naive approach. You may need more sophisticated regex for complex cases
                content = content.replace('url_for(\'static\'', './static')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

def create_mock_api_responses():
    """Create mock JSON responses for API endpoints"""
    print("Creating mock API responses...")
    
    api_dir = os.path.join(OUTPUT_DIR, 'api')
    if not os.path.exists(api_dir):
        os.makedirs(api_dir)
    
    # Mock response for check-location
    check_location_response = {
        "allowed": True,
        "message": "Ваше местоположение подтверждено!"
    }
    with open(os.path.join(api_dir, 'check-location.json'), 'w', encoding='utf-8') as f:
        json.dump(check_location_response, f, ensure_ascii=False, indent=4)
    
    # Mock response for check-phone
    check_phone_response = {
        "registered": False,
        "message": "Номер телефона доступен для регистрации"
    }
    with open(os.path.join(api_dir, 'check-phone.json'), 'w', encoding='utf-8') as f:
        json.dump(check_phone_response, f, ensure_ascii=False, indent=4)

def create_client_side_script():
    """Create JavaScript file to handle form submissions client-side"""
    print("Creating client-side script for form handling...")
    
    js_content = """
    document.addEventListener('DOMContentLoaded', function() {
        // Handle request location button
        const requestLocationBtn = document.getElementById('request-location');
        if (requestLocationBtn) {
            requestLocationBtn.addEventListener('click', function() {
                // Mock successful location check
                document.getElementById('location-status').innerHTML = 
                    '<div class="alert alert-success">Ваше местоположение подтверждено!</div>';
                document.getElementById('next-step-container').style.display = 'block';
                document.getElementById('user-city-display').classList.remove('d-none');
                document.getElementById('user-city-name').textContent = 'Карабудахкент';
            });
        }
        
        // Handle proceed to registration button
        const proceedBtn = document.getElementById('proceed-to-registration');
        if (proceedBtn) {
            proceedBtn.addEventListener('click', function() {
                document.getElementById('location-step').style.display = 'none';
                document.getElementById('registration-step').style.display = 'block';
                document.getElementById('confirmed-city-name').textContent = 'Карабудахкент';
            });
        }
        
        // Handle back button
        const backBtn = document.getElementById('back-to-location');
        if (backBtn) {
            backBtn.addEventListener('click', function() {
                document.getElementById('registration-step').style.display = 'none';
                document.getElementById('location-step').style.display = 'block';
            });
        }
        
        // Handle registration form
        const regForm = document.getElementById('registration-form');
        if (regForm) {
            regForm.addEventListener('submit', function(e) {
                e.preventDefault();
                window.location.href = 'success.html';
            });
        }
        
        // Handle ticket search form
        const ticketSearchForm = document.getElementById('ticketSearch');
        if (ticketSearchForm) {
            ticketSearchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const resultDiv = document.getElementById('ticketSearchResult');
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <h5 class="mb-2">Найден билет:</h5>
                        <p class="mb-0">Номер билета: <strong>ABC12345</strong></p>
                    </div>
                `;
                resultDiv.style.display = 'block';
            });
        }
    });
    """
    
    js_dir = os.path.join(OUTPUT_DIR, 'static', 'js')
    if not os.path.exists(js_dir):
        os.makedirs(js_dir)
    
    with open(os.path.join(js_dir, 'static-app.js'), 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    # Create a script element reference in all HTML files
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '</body>' in content and 'static-app.js' not in content:
                    content = content.replace('</body>', 
                        '<script src="static/js/static-app.js"></script></body>')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

def create_github_repository(username, token, repo_name, description="Porsche Giveaway Website"):
    """Create a new GitHub repository"""
    print(f"Creating GitHub repository: {repo_name}...")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "homepage": f"https://{username}.github.io/{repo_name}",
        "private": False,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "auto_init": False
    }
    
    response = requests.post(f"{GITHUB_API_URL}/user/repos", headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Repository created successfully: {response.json()['html_url']}")
        return response.json()
    else:
        if response.status_code == 422:
            print(f"Repository '{repo_name}' already exists, continuing...")
            return {"name": repo_name, "full_name": f"{username}/{repo_name}"}
        else:
            print(f"Failed to create repository. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

def upload_files_to_github(username, token, repo_name, dir_path):
    """Upload files to GitHub repository"""
    print(f"Uploading files to GitHub repository: {repo_name}...")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Walk through the build directory and upload all files
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, dir_path)
            
            # Skip large files
            if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB
                print(f"Skipping large file: {rel_path}")
                continue
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Encode content to Base64
            encoded_content = base64.b64encode(content).decode('utf-8')
            
            # Create directory structure if needed
            dir_part = os.path.dirname(rel_path)
            if dir_part:
                dir_parts = dir_part.split(os.path.sep)
                current_path = ""
                for part in dir_parts:
                    if current_path:
                        current_path = f"{current_path}/{part}"
                    else:
                        current_path = part
                    
                    # Check if directory exists
                    dir_url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{current_path}"
                    dir_response = requests.get(dir_url, headers=headers)
                    
                    if dir_response.status_code == 404:
                        # Create directory by creating a .gitkeep file
                        gitkeep_data = {
                            "message": f"Create directory {current_path}",
                            "content": base64.b64encode(b"").decode('utf-8'),
                            "branch": "main"
                        }
                        requests.put(
                            f"{dir_url}/.gitkeep",
                            headers=headers, 
                            json=gitkeep_data
                        )
            
            # Prepare data for API request
            file_url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{rel_path.replace(os.path.sep, '/')}"
            file_data = {
                "message": f"Add {rel_path}",
                "content": encoded_content,
                "branch": "main"
            }
            
            # Check if file exists to update it instead of creating new
            check_response = requests.get(file_url, headers=headers)
            if check_response.status_code == 200:
                file_data["sha"] = check_response.json()["sha"]
                print(f"Updating file: {rel_path}")
            else:
                print(f"Creating file: {rel_path}")
            
            # Upload file
            response = requests.put(file_url, headers=headers, json=file_data)
            
            if response.status_code not in [200, 201]:
                print(f"Failed to upload {rel_path}. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                # Don't exit, try to upload other files
            
            # GitHub API rate limiting
            time.sleep(0.5)
    
    print("Files uploaded successfully!")

def configure_github_pages(username, token, repo_name):
    """Configure GitHub Pages for the repository"""
    print(f"Configuring GitHub Pages for repository: {repo_name}...")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    
    response = requests.post(
        f"{GITHUB_API_URL}/repos/{username}/{repo_name}/pages",
        headers=headers, 
        json=data
    )
    
    if response.status_code in [201, 204]:
        print(f"GitHub Pages configured successfully!")
        print(f"Your site will be available at: https://{username}.github.io/{repo_name}")
        return True
    else:
        print(f"Failed to configure GitHub Pages. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Main function to generate static site and deploy to GitHub Pages"""
    print("Starting static site generation for GitHub Pages...")
    
    # Clean output directory if it exists
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    try:
        # Setup and run the freezer
        freezer = setup_freezer()
        freezer.freeze()
        print(f"Static site generated in directory: {OUTPUT_DIR}")
        
        # Post-process the static files
        modify_static_files()
        fix_urls_in_html()
        create_mock_api_responses()
        create_client_side_script()
        
        # Ask user if they want to deploy to GitHub
        deploy = input("Do you want to deploy to GitHub Pages? (y/n): ").lower()
        if deploy != 'y':
            print("Deployment skipped. You can find the static site in the 'build' directory.")
            return
        
        # Get GitHub credentials
        username = input("Enter your GitHub username: ")
        token = input("Enter your GitHub personal access token: ")
        repo_name = input("Enter the name for your GitHub repository: ") or "porsche-giveaway"
        
        # Create GitHub repository
        repo = create_github_repository(username, token, repo_name)
        if not repo:
            print("Failed to create repository. Exiting.")
            return
        
        # Upload files to GitHub
        upload_files_to_github(username, token, repo_name, OUTPUT_DIR)
        
        # Configure GitHub Pages
        configure_github_pages(username, token, repo_name)
        
        print("\nDeployment completed!")
        print(f"Repository URL: https://github.com/{username}/{repo_name}")
        print(f"GitHub Pages URL: https://{username}.github.io/{repo_name}")
        print("\nNOTE: It may take a few minutes for GitHub Pages to build and deploy your site.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 