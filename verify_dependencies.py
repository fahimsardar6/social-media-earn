import pkg_resources
import sys

required_packages = {
    'fastapi': '0.68.0',
    'uvicorn': '0.15.0',
    'newsapi-python': '0.2.6',
    'moviepy': '1.0.3',
    'python-multipart': '0.0.5',
    'newspaper3k': '0.2.8',
    'requests': '2.26.0'
}

def check_dependencies():
    missing = []
    outdated = []
    
    for package, min_version in required_packages.items():
        try:
            installed = pkg_resources.get_distribution(package)
            if pkg_resources.parse_version(installed.version) < pkg_resources.parse_version(min_version):
                outdated.append(f"{package} (installed: {installed.version}, required: {min_version})")
        except pkg_resources.DistributionNotFound:
            missing.append(package)
    
    if missing or outdated:
        print("\nDependency Check Failed!")
        if missing:
            print("\nMissing packages:")
            print("\n".join(f"- {pkg}" for pkg in missing))
            print("\nInstall missing packages with:")
            print(f"pip install {' '.join(missing)}")
        
        if outdated:
            print("\nOutdated packages:")
            print("\n".join(f"- {pkg}" for pkg in outdated))
            print("\nUpdate outdated packages with:")
            print(f"pip install --upgrade {' '.join(pkg.split()[0] for pkg in outdated)}")
        sys.exit(1)
    else:
        print("All dependencies are installed and up to date!")
        return True

if __name__ == "__main__":
    print("Checking dependencies...")
    check_dependencies()
