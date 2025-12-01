import cv2
import numpy as np
import os

def create_demo_video():
    # Paths
    assets_dir = "/home/takahashi/.gemini/antigravity/brain/b80bac28-2bea-4f7f-9c93-52cd8454e02d"
    output_path = "frontend/public/demo.mp4"
    
    # Load assets
    bg_path = os.path.join(assets_dir, "office_background_1764622485155.png")
    hand_point_path = os.path.join(assets_dir, "hand_pointing_green_screen_1764622439636.png")
    hand_palm_path = os.path.join(assets_dir, "hand_open_palm_green_screen_1764622450922.png")
    
    # Check if files exist (I'll need to list dir to get exact names if I guessed wrong)
    # For now, I'll assume I can find them.
    
    bg = cv2.imread(bg_path)
    hand_point = cv2.imread(hand_point_path)
    hand_palm = cv2.imread(hand_palm_path)
    
    if bg is None or hand_point is None or hand_palm is None:
        print("Error loading assets")
        return

    # Resize assets
    width, height = 640, 480
    bg = cv2.resize(bg, (width, height))
    
    # Resize hands to reasonable size (e.g. 200px height)
    hand_h = 250
    scale_point = hand_h / hand_point.shape[0]
    hand_point = cv2.resize(hand_point, (int(hand_point.shape[1] * scale_point), hand_h))
    
    scale_palm = hand_h / hand_palm.shape[0]
    hand_palm = cv2.resize(hand_palm, (int(hand_palm.shape[1] * scale_palm), hand_h))

    # Video Writer - Use H.264 for better browser compatibility
    # Try x264 first, fallback to mp4v if not available
    try:
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
    except:
        try:
            fourcc = cv2.VideoWriter_fourcc(*'H264')  # Alternative H.264
        except:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Fallback
            print("WARNING: H.264 not available, using mp4v (may not work in all browsers)")
    
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
    
    # Animation parameters
    duration = 10 # seconds
    total_frames = 30 * duration
    
    center_x, center_y = width // 2, height // 2
    radius = 100
    
    print(f"Generating video to {output_path}...")
    
    for i in range(total_frames):
        frame = bg.copy()
        t = i / 30.0
        
        # Determine state
        if t < 2.0:
            # Phase 1: Hover (Palm) moving to center
            current_hand = hand_palm
            progress = t / 2.0
            x = int(width * 0.8 * (1 - progress) + (center_x + radius) * progress)
            y = int(height * 0.8 * (1 - progress) + center_y * progress)
            
        elif t < 8.0:
            # Phase 2: Draw (Point) in circle
            current_hand = hand_point
            angle = (t - 2.0) * 2 # Speed
            x = int(center_x + radius * np.cos(angle))
            y = int(center_y + radius * np.sin(angle))
            
        else:
            # Phase 3: Hover (Palm) moving away
            current_hand = hand_palm
            progress = (t - 8.0) / 2.0
            x = int((center_x + radius) * (1 - progress) + width * 0.8 * progress)
            y = int(center_y * (1 - progress) + height * 0.8 * progress)

        # Overlay hand (Green screen removal)
        h, w = current_hand.shape[:2]
        
        # Top-left position
        y1 = y - h // 2
        x1 = x - w // 2
        y2 = y1 + h
        x2 = x1 + w
        
        # Bounds check
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0
        if x2 > width: x2 = width
        if y2 > height: y2 = height
        
        # Dimensions of overlay
        oh = y2 - y1
        ow = x2 - x1
        
        if oh > 0 and ow > 0:
            hand_crop = current_hand[0:oh, 0:ow] # Simplified crop
            
            # Chroma key (remove green)
            # Green is roughly [0, 255, 0] in BGR? No, in BGR it's [0, 255, 0]
            # Let's use HSV for better masking
            hsv = cv2.cvtColor(hand_crop, cv2.COLOR_BGR2HSV)
            # Green range
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            mask_inv = cv2.bitwise_not(mask)
            
            # Black-out area in bg
            roi = frame[y1:y2, x1:x2]
            bg_bg = cv2.bitwise_and(roi, roi, mask=mask) # Wait, mask is green. We want NOT green.
            # Actually:
            # Mask = Green pixels (255)
            # Mask_inv = Non-green pixels (255) -> Hand
            
            img_bg = cv2.bitwise_and(roi, roi, mask=mask) # The background where hand is NOT
            img_fg = cv2.bitwise_and(hand_crop, hand_crop, mask=mask_inv) # The hand
            
            dst = cv2.add(img_bg, img_fg)
            frame[y1:y2, x1:x2] = dst

        out.write(frame)
        
    out.release()
    print("Video generated!")

if __name__ == "__main__":
    create_demo_video()
