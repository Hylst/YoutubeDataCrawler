#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Dependencies Script

Intelligent dependency installer for YouTube Data Analyzer.
Handles problematic packages and provides fallback options.
"""

import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartInstaller:
    """
    Intelligent package installer with error handling and fallbacks.
    """
    
    def __init__(self):
        self.python_version = sys.version_info
        self.failed_packages = []
        self.successful_packages = []
        self.skipped_packages = []
        
    def check_python_version(self) -> bool:
        """
        Check if Python version is compatible.
        
        Returns:
            bool: True if compatible, False otherwise
        """
        if self.python_version >= (3, 8):
            logger.info(f"Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro} detected - Compatible")
            return True
        else:
            logger.error(f"Python {self.python_version.major}.{self.python_version.minor} detected - Requires Python 3.8+")
            return False
    
    def install_package(self, package: str, optional: bool = False) -> bool:
        """
        Install a single package with error handling.
        
        Args:
            package (str): Package name to install
            optional (bool): Whether the package is optional
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {package}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            self.successful_packages.append(package)
            logger.info(f"✅ Successfully installed {package}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⏰ Timeout installing {package}")
            self.failed_packages.append(package)
            return False
            
        except subprocess.CalledProcessError as e:
            if optional:
                logger.warning(f"⚠️  Optional package {package} failed to install: {e.stderr.strip()}")
                self.skipped_packages.append(package)
            else:
                logger.error(f"❌ Failed to install {package}: {e.stderr.strip()}")
                self.failed_packages.append(package)
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error installing {package}: {str(e)}")
            self.failed_packages.append(package)
            return False
    
    def install_core_packages(self) -> bool:
        """
        Install core packages required for basic functionality.
        
        Returns:
            bool: True if all core packages installed successfully
        """
        core_packages = [
            'google-api-python-client>=2.0.0',
            'requests>=2.28.0',
            'python-dotenv>=0.19.0',
            'pandas>=2.0.0',
            'numpy>=1.24.0',
            'Pillow>=10.0.0',
            'pydantic>=2.0.0',
            'pydantic-settings>=2.0.0',
            'coloredlogs>=15.0.0',
            'click>=8.0.0',
            'rich>=13.0.0',
            'tqdm>=4.65.0'
        ]
        
        logger.info("Installing core packages...")
        success_count = 0
        
        for package in core_packages:
            if self.install_package(package):
                success_count += 1
        
        success_rate = success_count / len(core_packages)
        logger.info(f"Core packages: {success_count}/{len(core_packages)} installed ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80% success rate required
    
    def install_ui_packages(self) -> bool:
        """
        Install UI packages (PyQt6 and Streamlit).
        
        Returns:
            bool: True if at least one UI framework is available
        """
        ui_packages = [
            ('PyQt6>=6.4.0', False),
            ('streamlit>=1.29.0', False)
        ]
        
        logger.info("Installing UI packages...")
        ui_success = False
        
        for package, optional in ui_packages:
            if self.install_package(package, optional):
                ui_success = True
        
        if not ui_success:
            logger.warning("⚠️  No UI frameworks installed successfully")
        
        return ui_success
    
    def install_optional_packages(self) -> None:
        """
        Install optional packages with graceful failure handling.
        """
        optional_packages = [
            'orjson>=3.8.0',
            'openpyxl>=3.1.0',
            'plotly>=5.15.0',
            'altair>=5.0.0',
            'httpx>=0.24.0',
            'pytz>=2022.1',
            'pyyaml>=6.0',
            'toml>=0.10.2',
            'opencv-python>=4.8.0',
            'matplotlib>=3.7.0',
            'seaborn>=0.12.0',
            'python-decouple>=3.8'
        ]
        
        logger.info("Installing optional packages...")
        
        for package in optional_packages:
            self.install_package(package, optional=True)
    
    def install_ai_packages(self) -> None:
        """
        Install AI/ML packages (all optional).
        """
        ai_packages = [
            'openai>=1.0.0',
            'anthropic>=0.3.0',
            'google-generativeai>=0.3.0'
        ]
        
        logger.info("Installing AI/ML packages (optional)...")
        
        for package in ai_packages:
            self.install_package(package, optional=True)
    
    def generate_report(self) -> str:
        """
        Generate installation report.
        
        Returns:
            str: Formatted report
        """
        report = []
        report.append("=" * 60)
        report.append("DEPENDENCY INSTALLATION REPORT")
        report.append("=" * 60)
        
        if self.successful_packages:
            report.append(f"\n✅ Successfully installed ({len(self.successful_packages)}):")
            for pkg in self.successful_packages:
                report.append(f"   • {pkg}")
        
        if self.skipped_packages:
            report.append(f"\n⚠️  Skipped optional packages ({len(self.skipped_packages)}):")
            for pkg in self.skipped_packages:
                report.append(f"   • {pkg}")
        
        if self.failed_packages:
            report.append(f"\n❌ Failed to install ({len(self.failed_packages)}):")
            for pkg in self.failed_packages:
                report.append(f"   • {pkg}")
        
        total = len(self.successful_packages) + len(self.skipped_packages) + len(self.failed_packages)
        success_rate = len(self.successful_packages) / total if total > 0 else 0
        
        report.append(f"\nSUMMARY:")
        report.append(f"Success rate: {success_rate:.1%}")
        
        if self.failed_packages:
            report.append("\n⚠️  Some packages failed to install.")
            report.append("   You may need to install them manually or check system dependencies.")
        else:
            report.append("\n🎉 All packages installed successfully!")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """
    Main installation function.
    """
    installer = SmartInstaller()
    
    # Check Python version
    if not installer.check_python_version():
        sys.exit(1)
    
    logger.info("Starting intelligent dependency installation...")
    
    # Install packages in order of importance
    core_success = installer.install_core_packages()
    ui_success = installer.install_ui_packages()
    
    if not core_success:
        logger.error("❌ Critical: Core packages installation failed")
        print(installer.generate_report())
        sys.exit(1)
    
    if not ui_success:
        logger.warning("⚠️  Warning: No UI frameworks available")
    
    # Install optional packages
    installer.install_optional_packages()
    installer.install_ai_packages()
    
    # Generate and display report
    print(installer.generate_report())
    
    if installer.failed_packages:
        logger.info("\n💡 Tip: Run 'python setup_dependencies.py' again to retry failed packages")
        sys.exit(1)
    else:
        logger.info("\n🚀 Ready to run the application!")
        logger.info("   Try: python main.py")
        logger.info("   Or:  streamlit run ui/streamlit_app.py")


if __name__ == '__main__':
    main()