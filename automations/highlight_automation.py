import cv2
import numpy as np

def run(detected_object, frame, confidence, **kwargs):
    coords = kwargs.get('coords')
    if coords is None:
        return False
        
    x1, y1, x2, y2 = [int(c) for c in coords[:4]]
    
    colors = {
        'person': (0, 0, 255),    # Red
        'car': (255, 165, 0),     # Blue-ish
        'dog': (0, 255, 0),       # Green
        'cat': (255, 0, 255),     # Purple
        'bottle': (0, 255, 255),  # Yellow
        'chair': (255, 255, 0)    # Cyan
    }
    
    color = colors.get(detected_object, (255, 255, 255))
    
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    
    text = f"{detected_object.upper()} DETECTED!"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
    cv2.rectangle(frame, (x1, y1 - text_size[1] - 10), (x1 + text_size[0], y1), color, -1)
    
    cv2.putText(frame, text, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    return True