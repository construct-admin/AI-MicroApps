"""
Image processing utilities for Visual Transcription app
"""
import cv2
import numpy as np
import os
import tempfile
import base64
import streamlit as st
from PIL import Image

def image_to_base64(image):
    """Convert PIL image or numpy array to base64 string."""
    try:
        if isinstance(image, np.ndarray):
            try:
                image = Image.fromarray(image)
            except Exception as conversion_error:
                st.error(f"Error converting array to image: {conversion_error}")
                return ""
        
        try:
            buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            image.save(buffered, format="JPEG")
            
            try:
                with open(buffered.name, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as read_error:
                st.error(f"Error reading image file: {read_error}")
                return ""
            finally:
                # Ensure temp file is cleaned up even if there's an error
                try:
                    os.unlink(buffered.name)
                except:
                    pass
        except Exception as save_error:
            st.error(f"Error saving image to temporary file: {save_error}")
            return ""
    except Exception as e:
        st.error(f"Error in image_to_base64: {e}")
        return ""

def encode_image(image):
    """Encode a PIL image as base64."""
    try:
        if image is None:
            st.error("No image provided for encoding")
            return ""
            
        try:
            buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            
            try:
                image.save(buffered, format="JPEG")
            except Exception as save_error:
                st.error(f"Error saving image: {save_error}")
                return ""
                
            try:
                with open(buffered.name, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode("utf-8")
                    return encoded
            except Exception as read_error:
                st.error(f"Error reading/encoding image: {read_error}")
                return ""
            finally:
                # Clean up temp file
                try:
                    os.unlink(buffered.name)
                except:
                    pass
        except Exception as temp_error:
            st.error(f"Error creating temporary file: {temp_error}")
            return ""
    except Exception as e:
        st.error(f"Error in encode_image: {e}")
        return ""

def get_frame_timestamp(frame_number, video_obj):
    """Get timestamp for a frame."""
    try:
        if video_obj is None:
            return 0
            
        if not isinstance(video_obj, cv2.VideoCapture):
            st.warning("Invalid video object type")
            return 0
            
        if not video_obj.isOpened():
            st.warning("Video object is not open")
            return 0
            
        fps = video_obj.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            st.warning("Invalid FPS value in video")
            return 0
            
        seconds = frame_number / fps
        return seconds
    except Exception as e:
        st.error(f"Error getting frame timestamp: {e}")
        return 0

def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    try:
        if seconds is None:
            return "00:00:00"
            
        if not isinstance(seconds, (int, float)):
            seconds = float(seconds)  # Try to convert
            
        if seconds < 0:
            seconds = 0  # Ensure non-negative
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02}:{minutes:02}:{secs:02}"
    except Exception as e:
        st.warning(f"Error converting seconds to timestamp: {e}")
        return "00:00:00"

def crop_rectangular(image_cv_bgr, rect_data):
    """Crops the OpenCV BGR image using rectangle data."""
    try:
        # Validate input image
        if image_cv_bgr is None:
            st.error("No image provided for cropping")
            return None
            
        if not isinstance(image_cv_bgr, np.ndarray):
            st.error("Invalid image format for cropping")
            return None
            
        # Check if image has valid dimensions
        if len(image_cv_bgr.shape) < 2:
            st.error("Invalid image dimensions for cropping")
            return None
            
        # Validate rectangle data
        if rect_data is None or not isinstance(rect_data, dict):
            st.error("Invalid rectangle data for cropping")
            return None
            
        # Check if all required keys exist
        required_keys = ['left', 'top', 'width', 'height']
        for key in required_keys:
            if key not in rect_data:
                st.error(f"Missing '{key}' in rectangle data")
                return None
        
        try:
            left = int(rect_data['left'])
            top = int(rect_data['top'])
            width = int(rect_data['width'])
            height = int(rect_data['height'])
        except (ValueError, TypeError) as conversion_error:
            st.error(f"Invalid rectangle dimensions: {conversion_error}")
            return None
            
        # Validate dimensions
        if width <= 0 or height <= 0:
            st.warning("Please draw a valid rectangle with non-zero dimensions.")
            return None
            
        # Get image dimensions and validate
        try:
            h_img, w_img = image_cv_bgr.shape[:2]
        except Exception as shape_error:
            st.error(f"Error getting image dimensions: {shape_error}")
            return None
            
        # Clamp coordinates to image boundaries
        x1, y1 = max(0, left), max(0, top)
        x2, y2 = min(w_img, left + width), min(h_img, top + height)
        
        if x2 <= x1 or y2 <= y1:
             st.warning("Calculated crop area is outside image bounds or invalid.")
             return None
             
        # Perform the actual crop
        try:
            cropped_bgr = image_cv_bgr[y1:y2, x1:x2]
            
            # Validate crop result
            if cropped_bgr.size == 0:
                st.warning("Cropping resulted in an empty image.")
                return None
                
            return cropped_bgr
        except Exception as crop_error:
            st.error(f"Error during image cropping: {crop_error}")
            return None
    except Exception as e:
        st.error(f"Unexpected error in rectangular cropping: {e}")
        return None

def crop_freeform(image_cv_bgr, path_data):
    """Crops the OpenCV BGR image using freeform path data."""
    try:
        # Validate input image
        if image_cv_bgr is None:
            st.error("No image provided for freeform cropping")
            return None
            
        if not isinstance(image_cv_bgr, np.ndarray):
            st.error("Invalid image format for freeform cropping")
            return None
            
        # Check if image has valid dimensions
        if len(image_cv_bgr.shape) < 2:
            st.error("Invalid image dimensions for freeform cropping")
            return None
            
        # Validate path data
        if not path_data:
             st.warning("Received empty path data for freeform cropping.")
             return None
             
        if not isinstance(path_data, list):
            st.error("Invalid path data format for freeform cropping")
            return None
    
        # Get image dimensions for boundary validation
        try:
            h_img, w_img = image_cv_bgr.shape[:2]
        except Exception as shape_error:
            st.error(f"Error getting image dimensions: {shape_error}")
            return None
        
        points_list = []
        for point_idx, point_cmd in enumerate(path_data):
            try:
                if not isinstance(point_cmd, list):
                    continue
                    
                if len(point_cmd) < 3:
                    continue
                    
                # Extract coordinates
                try:
                    x = int(float(point_cmd[-2]))
                    y = int(float(point_cmd[-1]))
                except (ValueError, TypeError, IndexError) as coord_error:
                    # Skip invalid coordinates silently
                    continue
                
                # Clip coordinates to image boundaries
                x = max(0, min(x, w_img - 1))
                y = max(0, min(y, h_img - 1))
                
                # Add the valid point to our list
                points_list.append([x, y])
            except Exception as point_error:
                # Skip problematic points but log the error
                st.warning(f"Error processing point {point_idx}: {point_error}")
                continue

        # Ensure we have enough points to form a shape
        if len(points_list) < 3:
             st.warning("Not enough valid points to create a freeform crop area. Please try again with a more complete shape.")
             return None
        
        try:
            # Convert to numpy array for OpenCV
            contour = np.array(points_list, dtype=np.int32)
            
            # Create a mask with only the points inside the image
            try:
                mask = np.zeros(image_cv_bgr.shape[:2], dtype=np.uint8)
            except Exception as mask_error:
                st.error(f"Error creating mask: {mask_error}")
                return None
                
            try:
                cv2.drawContours(mask, [contour], -1, color=255, thickness=cv2.FILLED)
            except Exception as contour_error:
                st.error(f"Error drawing contours: {contour_error}")
                return None
            
            # Apply the mask
            try:
                masked_image_bgr = cv2.bitwise_and(image_cv_bgr, image_cv_bgr, mask=mask)
            except Exception as mask_apply_error:
                st.error(f"Error applying mask: {mask_apply_error}")
                return None
            
            # Calculate bounding rectangle
            try:
                x_bb, y_bb, w_bb, h_bb = cv2.boundingRect(contour)
            except Exception as bounds_error:
                st.error(f"Error calculating bounding rectangle: {bounds_error}")
                return None
            
            # Validate bounding box dimensions
            if w_bb <= 0 or h_bb <= 0:
                st.warning("Freeform crop area resulted in an empty image. Please try a larger selection.")
                return None
                
            # Ensure bounding box is within image boundaries
            x_bb = max(0, x_bb)
            y_bb = max(0, y_bb)
            w_bb = min(w_bb, w_img - x_bb)
            h_bb = min(h_bb, h_img - y_bb)
            
            # Final validation of crop area
            if w_bb <= 0 or h_bb <= 0:
                st.warning("Crop area is outside image boundaries. Please try again.")
                return None
                
            # Extract the bounded region
            try:
                cropped_bgr = masked_image_bgr[y_bb:y_bb+h_bb, x_bb:x_bb+w_bb]
                
                # Validate the final crop
                if cropped_bgr.size == 0:
                    st.warning("Freeform cropping resulted in an empty image.")
                    return None
                    
                # Check if the crop contains any non-zero pixels
                if np.count_nonzero(cropped_bgr) == 0:
                    st.warning("Freeform crop contains only black pixels. Please try a different selection.")
                    return None
                    
                return cropped_bgr
            except Exception as crop_error:
                st.error(f"Error extracting cropped region: {crop_error}")
                return None
        
        except Exception as processing_error:
            st.error(f"Error during freeform crop processing: {processing_error}")
            return None
    
    except Exception as e:
        st.error(f"Unexpected error during freeform cropping: {e}")
        return None 