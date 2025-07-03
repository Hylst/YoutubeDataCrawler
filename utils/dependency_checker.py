# -*- coding: utf-8 -*-
"""
Dependency Checker Utility

Automatically validates and installs missing packages for the YouTube Data Analyzer.
"""

import subprocess
import sys
import importlib
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DependencyChecker:
    """
    Manages dependency checking and installation for the application.
    """
    
    # Core dependencies mapping: import_name -> package_name
    CORE_DEPENDENCIES = {
        'googleapiclient': 'google-api-python-client',
        'PyQt6': 'PyQt6',
        'streamlit': 'streamlit',
        'dotenv': 'python-dotenv',
        'requests': 'requests',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'speech_recognition': 'SpeechRecognition',
        'pyaudio': 'pyaudio',
        'pydantic': 'pydantic',
        'coloredlogs': 'coloredlogs'
    }
    
    # Built-in modules that don't need installation
    BUILTIN_MODULES = {
        'sqlite3': 'Built into Python',
        'json': 'Built into Python',
        'os': 'Built into Python',
        'sys': 'Built into Python',
        'pathlib': 'Built into Python'
    }
    
    # Optional dependencies
    OPTIONAL_DEPENDENCIES = {
        'pytest': 'pytest',
        'black': 'black',
        'flake8': 'flake8',
        'mypy': 'mypy'
    }
    
    def __init__(self):
        """
        Initialize the dependency checker.
        """
        self.missing_core = []
        self.missing_optional = []
        self.available_core = []
        self.available_optional = []
    
    def check_dependency(self, import_name: str) -> bool:
        """
        Check if a specific dependency is available.
        
        Args:
            import_name (str): The import name of the module
            
        Returns:
            bool: True if dependency is available, False otherwise
        """
        try:
            importlib.import_module(import_name)
            return True
        except ImportError:
            return False
    
    def check_all_dependencies(self) -> Dict[str, List[str]]:
        """
        Check all core and optional dependencies.
        
        Returns:
            Dict[str, List[str]]: Status of all dependencies
        """
        logger.info("Checking dependencies...")
        
        # Check core dependencies
        for import_name, package_name in self.CORE_DEPENDENCIES.items():
            if self.check_dependency(import_name):
                self.available_core.append(package_name)
                logger.debug(f"✓ {package_name} is available")
            else:
                self.missing_core.append(package_name)
                logger.warning(f"✗ {package_name} is missing")
        
        # Check optional dependencies
        for import_name, package_name in self.OPTIONAL_DEPENDENCIES.items():
            if self.check_dependency(import_name):
                self.available_optional.append(package_name)
                logger.debug(f"✓ {package_name} (optional) is available")
            else:
                self.missing_optional.append(package_name)
                logger.info(f"○ {package_name} (optional) is missing")
        
        return {
            'missing_core': self.missing_core,
            'missing_optional': self.missing_optional,
            'available_core': self.available_core,
            'available_optional': self.available_optional
        }
    
    def install_package(self, package_name: str) -> bool:
        """
        Install a specific package using pip.
        
        Args:
            package_name (str): Name of the package to install
            
        Returns:
            bool: True if installation successful, False otherwise
        """
        # Check if it's a built-in module
        if package_name in self.BUILTIN_MODULES:
            logger.info(f"Skipping {package_name} - {self.BUILTIN_MODULES[package_name]}")
            return True
            
        try:
            logger.info(f"Installing {package_name}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Successfully installed {package_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {package_name}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing {package_name}: {str(e)}")
            return False
    
    def install_missing_core(self) -> Tuple[List[str], List[str]]:
        """
        Install all missing core dependencies.
        
        Returns:
            Tuple[List[str], List[str]]: (successfully_installed, failed_to_install)
        """
        if not self.missing_core:
            logger.info("All core dependencies are already installed")
            return [], []
        
        successfully_installed = []
        failed_to_install = []
        
        for package in self.missing_core:
            if self.install_package(package):
                successfully_installed.append(package)
            else:
                failed_to_install.append(package)
        
        return successfully_installed, failed_to_install
    
    def install_from_requirements(self, requirements_file: Optional[Path] = None) -> bool:
        """
        Install dependencies from requirements.txt file.
        
        Args:
            requirements_file (Optional[Path]): Path to requirements file
            
        Returns:
            bool: True if installation successful, False otherwise
        """
        if requirements_file is None:
            requirements_file = Path(__file__).parent.parent / 'requirements.txt'
        
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        try:
            logger.info(f"Installing dependencies from {requirements_file}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Successfully installed dependencies from requirements.txt")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install from requirements.txt: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
    
    def get_dependency_report(self) -> str:
        """
        Generate a comprehensive dependency report.
        
        Returns:
            str: Formatted dependency report
        """
        report = []
        report.append("=" * 60)
        report.append("DEPENDENCY REPORT")
        report.append("=" * 60)
        
        # Core dependencies
        report.append("\nCORE DEPENDENCIES:")
        report.append("-" * 20)
        
        if self.available_core:
            report.append("✓ Available:")
            for dep in self.available_core:
                report.append(f"  • {dep}")
        
        if self.missing_core:
            report.append("✗ Missing:")
            for dep in self.missing_core:
                report.append(f"  • {dep}")
        
        # Optional dependencies
        report.append("\nOPTIONAL DEPENDENCIES:")
        report.append("-" * 25)
        
        if self.available_optional:
            report.append("✓ Available:")
            for dep in self.available_optional:
                report.append(f"  • {dep}")
        
        if self.missing_optional:
            report.append("○ Missing:")
            for dep in self.missing_optional:
                report.append(f"  • {dep}")
        
        # Summary
        total_core = len(self.available_core) + len(self.missing_core)
        total_optional = len(self.available_optional) + len(self.missing_optional)
        
        report.append("\nSUMMARY:")
        report.append("-" * 10)
        report.append(f"Core: {len(self.available_core)}/{total_core} available")
        report.append(f"Optional: {len(self.available_optional)}/{total_optional} available")
        
        if self.missing_core:
            report.append("\n⚠️  CRITICAL: Missing core dependencies detected!")
            report.append("   Run: python -m utils.dependency_checker --install")
        else:
            report.append("\n✅ All core dependencies are satisfied")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """
    Main function for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Data Analyzer Dependency Checker')
    parser.add_argument('--install', action='store_true', help='Install missing core dependencies')
    parser.add_argument('--install-all', action='store_true', help='Install from requirements.txt')
    parser.add_argument('--report', action='store_true', help='Show dependency report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    checker = DependencyChecker()
    checker.check_all_dependencies()
    
    if args.install:
        success, failed = checker.install_missing_core()
        if failed:
            print(f"\n❌ Failed to install: {', '.join(failed)}")
            sys.exit(1)
        else:
            print("\n✅ All core dependencies installed successfully")
    
    elif args.install_all:
        if checker.install_from_requirements():
            print("\n✅ All dependencies installed from requirements.txt")
        else:
            print("\n❌ Failed to install from requirements.txt")
            sys.exit(1)
    
    elif args.report or not any([args.install, args.install_all]):
        print(checker.get_dependency_report())
        if checker.missing_core:
            sys.exit(1)


if __name__ == '__main__':
    main()