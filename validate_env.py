import sys
import platform
import importlib.util
import cv2

def check_package(package_name, min_version=None):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"[-] {package_name} NOT installed")
        return False
    
    try:
        module = __import__(package_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"[+] {package_name} installed (version: {version})")
        return True
    except ImportError:
        print(f"[-] {package_name} installed but failed to import")
        return False

def check_webcam():
    print("Checking webcam access...")
    # Try indices 0 to 3
    for i in range(4):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"[+] Webcam accessible at index {i}. Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                cap.release()
                return True
            cap.release()
    
    print("[-] Webcam NOT detected or accessible on indices 0-3")
    return False

def main():
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    print("\nChecking Libraries:")
    packages = ['mediapipe', 'cv2', 'numpy', 'PIL']
    all_packages_ok = all(check_package(p) for p in packages)
    
    print("\nChecking Hardware:")
    webcam_ok = check_webcam()
    
    if all_packages_ok and webcam_ok:
        print("\n[SUCCESS] Environment validation passed.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Environment validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
