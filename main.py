#!/usr/bin/env python3
"""
EXU CODER BOT - Complete Setup with Tor
"""

import os
import sys
import subprocess
import time
import platform

# Python packages (just names)
PACKAGES = [
    "pyTelegramBotAPI",
    "requests",
    "pycryptodome",
    "psutil",
    "Flask",
    "urllib3",
    "pysocks"
]

def install_packages():
    """Install all required Python packages"""
    print("\n📦 Installing Python packages...")
    
    for package in PACKAGES:
        print(f"  Installing {package}...")
        subprocess.run(f"{sys.executable} -m pip install {package}", 
                      shell=True, capture_output=True)
    
    print("✅ All Python packages installed!")

def install_tor():
    """Install Tor system service"""
    print("\n🔄 Installing Tor...")
    
    system = platform.system().lower()
    
    # Check if Tor is already installed
    try:
        subprocess.run("tor --version", shell=True, capture_output=True, check=True)
        print("✅ Tor is already installed")
        return True
    except:
        pass
    
    # Try to install Tor based on system
    try:
        if 'termux' in platform.platform().lower():
            # Termux (Android)
            print("  📱 Termux detected")
            subprocess.run("pkg install tor -y", shell=True, check=True)
            
        elif system == 'linux':
            # Linux
            if os.path.exists('/usr/bin/apt'):
                # Debian/Ubuntu
                print("  🐧 Debian/Ubuntu detected")
                subprocess.run("sudo apt update && sudo apt install tor -y", shell=True, check=True)
            elif os.path.exists('/usr/bin/pacman'):
                # Arch
                print("  🐧 Arch Linux detected")
                subprocess.run("sudo pacman -S tor --noconfirm", shell=True, check=True)
            else:
                print("  ⚠️  Please install Tor manually: sudo apt install tor")
                return False
                
        elif system == 'darwin':
            # macOS
            print("  🍎 macOS detected")
            subprocess.run("brew install tor", shell=True, check=True)
            
        else:
            print(f"  ⚠️  Unsupported system: {system}")
            print("  Please install Tor manually from: https://www.torproject.org/")
            return False
        
        print("✅ Tor installed successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to install Tor: {e}")
        print("  Please install Tor manually")
        return False

def start_tor():
    """Start Tor service"""
    print("\n🔄 Starting Tor service...")
    
    try:
        if 'termux' in platform.platform().lower():
            # Termux
            subprocess.Popen(['tor'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        else:
            # Linux/macOS
            subprocess.run("sudo systemctl start tor", shell=True, capture_output=True)
        
        time.sleep(3)
        print("✅ Tor is running")
        return True
    except:
        print("⚠️  Could not start Tor automatically")
        print("   Please start Tor manually with: tor")
        return False

def run_bot():
    """Run the main bot script"""
    print("\n🚀 Starting EXU CODER BOT...")
    time.sleep(2)
    
    if os.path.exists("bot.py"):
        subprocess.run(f"{sys.executable} bot.py", shell=True)
    else:
        print("❌ bot.py not found!")
        print("Please make sure bot.py is in the same directory")

if __name__ == "__main__":
    print("🔧 EXU CODER BOT Setup")
    print("=" * 50)
    
    # Install Python packages
    install_packages()
    
    # Install Tor (if possible)
    install_tor()
    
    # Try to start Tor
    start_tor()
    
    # Run the bot
    run_bot()
