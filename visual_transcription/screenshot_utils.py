import numpy as np
import cv2
RECHTANGULAR_CROP = False
# Global variables
cropping = False
ix, iy = -1, -1
ex, ey = -1, -1
ref_point = []
image_to_show = None # To hold the image with the rectangle drawn
image = None # Global reference to the original image loaded
is_mouse_pressed = False
last_point = None # For continuous drawing
drag_start_point = None # To store the initial point of a drag
contour_points = [] # To store points for freeform crop
image_to_show_continuous = None # Image copy for continuous drawing
clone_continuous = None # Store original for masking

# Mouse callback function for rectangular crop
def mouse_callback_rechtangular(event, x, y, flags, param):
    global ix, iy, ex, ey, cropping, ref_point, image_to_show, image

    if event == cv2.EVENT_LBUTTONDOWN:
        # Record starting coordinates and set cropping flag
        ix, iy = x, y
        ex, ey = x, y # Initialize end points
        cropping = True
        ref_point = [(x, y)]
        image_to_show = image.copy() # Start with a fresh copy for drawing

    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping:
            # Update end coordinates and draw rectangle on the copy
            ex, ey = x, y
            image_to_show = image.copy()
            cv2.rectangle(image_to_show, (ix, iy), (x, y), (0, 255, 0), 1)

    elif event == cv2.EVENT_LBUTTONUP:
        # Record ending coordinates, reset cropping flag
        ex, ey = x, y
        cropping = False
        ref_point.append((x, y))

        # Draw final rectangle
        image_to_show = image.copy()
        cv2.rectangle(image_to_show, (ix, iy), (ex, ey), (0, 255, 0), 1)

        # Perform crop if the rectangle is valid
        if len(ref_point) == 2 and ix != ex and iy != ey:
             # Ensure coordinates are ordered correctly (top-left, bottom-right)
            roi_x1 = min(ix, ex)
            roi_y1 = min(iy, ey)
            roi_x2 = max(ix, ex)
            roi_y2 = max(iy, ey)

            cropped_image = image[roi_y1:roi_y2, roi_x1:roi_x2]
            if cropped_image.size > 0:
                # Display cropped image in a new window
                cv2.imshow("Cropped", cropped_image)
                print("Cropped image displayed in 'Cropped' window.")
            else:
                print("Crop area resulted in an empty image.")
        # No need for an else here, just don't show the cropped window if invalid


# Updated mouse callback for continuous drawing and freeform crop
def mouse_callback_continuous(event, x, y, flags, param):
    global is_mouse_pressed, last_point, drag_start_point, contour_points, image_to_show_continuous, clone_continuous

    if event == cv2.EVENT_LBUTTONDOWN:
        is_mouse_pressed = True
        last_point = (x, y)
        drag_start_point = (x, y)
        contour_points = [(x, y)] # Start new contour
        print(f"Left mouse button pressed at: x={x}, y={y}")
        # Ensure image_to_show_continuous exists
        if image_to_show_continuous is None and clone_continuous is not None:
             image_to_show_continuous = clone_continuous.copy()

    elif event == cv2.EVENT_MOUSEMOVE:
        if is_mouse_pressed and last_point is not None and image_to_show_continuous is not None:
            cv2.line(image_to_show_continuous, last_point, (x, y), (0, 0, 255), 2) # Draw on display image
            last_point = (x, y)
            contour_points.append((x, y)) # Add point to contour

    elif event == cv2.EVENT_LBUTTONUP:
        if is_mouse_pressed and drag_start_point is not None and image_to_show_continuous is not None and clone_continuous is not None:
            # Add final point and draw closing line on display image
            final_point = (x, y)
            contour_points.append(final_point)
            print(f"Connecting start {drag_start_point} to end {final_point}")
            cv2.line(image_to_show_continuous, drag_start_point, final_point, (0, 0, 255), 2)

            # --- Freeform Crop Logic ---
            if len(contour_points) > 2: # Need at least 3 points for a contour
                mask = np.zeros_like(clone_continuous) # Black mask same size as original
                contour_np = np.array(contour_points, dtype=np.int32)

                # Draw the filled contour on the mask (white color)
                cv2.drawContours(mask, [contour_np], -1, (255, 255, 255), cv2.FILLED)

                # Convert mask to grayscale for bitwise_and
                mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

                # Apply mask to the *original* image copy
                masked_image = cv2.bitwise_and(clone_continuous, clone_continuous, mask=mask_gray)

                # Find bounding box of the contour
                x_bb, y_bb, w_bb, h_bb = cv2.boundingRect(contour_np)

                # Extract the ROI using the bounding box from the masked image
                if w_bb > 0 and h_bb > 0:
                    cropped_final = masked_image[y_bb:y_bb+h_bb, x_bb:x_bb+w_bb]
                    cv2.imshow("Freeform Cropped", cropped_final)
                    cv2.imwrite("cropped_image.png", cropped_final)
                    print("Freeform cropped image displayed.")
                else:
                    print("Freeform crop area is too small.")
            else:
                print("Not enough points drawn for a freeform crop.")
            # --- End Freeform Crop Logic ---

        # Reset state for next drawing/crop
        is_mouse_pressed = False
        last_point = None
        drag_start_point = None
        contour_points = [] # Clear points for next shape
        print(f"Left mouse button released at: x={x}, y={y}")


# Main part of the script
image = cv2.imread('image.png') # Load the image
if image is None:
    print("Error: Could not load base image 'image.png'. Exiting.")
    exit()

image = cv2.resize(image, (1080, 720))

if RECHTANGULAR_CROP:
    if image is None:
        print("Error: Could not load image 'white_board_image.png'. Make sure it's in the correct directory.")
    else:
        clone = image.copy() # Keep an original copy
        image_to_show = image.copy() # Initialize image to show
        cv2.namedWindow('Image')
        cv2.setMouseCallback('Image', mouse_callback_rechtangular)
        print("Click and drag to select a rectangle crop area. Press 'r' to reset, 'q' to quit.")
        while True:
            cv2.imshow('Image', image_to_show) # Show the image (potentially with rectangle)
            key = cv2.waitKey(1) & 0xFF
            # Reset the cropping selection if 'r' is pressed
            if key == ord("r"):
                image_to_show = clone.copy() # Reset to original image display
                ref_point = [] # Clear points
                cropping = False # Ensure cropping is off
                # Optionally close the cropped window if it exists
                # cv2.destroyWindow("Cropped") # Might cause error if not open, better to just let it be replaced
                print("Crop reset. Select a new area.")
            # Quit if 'q' is pressed
            elif key == ord("q"):
                break
        cv2.destroyAllWindows()
else:
    # Continuous drawing / Freeform Crop mode
    # Make copies for drawing and resetting
    clone_continuous = image.copy() # Keep original safe for masking
    image_to_show_continuous = image.copy() # Image to draw lines on

    # Mask is created on demand in the callback now
    # mask = np.zeros(image.shape, dtype=np.uint8) # No longer needed here

    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', mouse_callback_continuous)
    print("Click and drag to draw a shape for cropping. Press 'r' to reset drawing, 'q' to quit.")

    while True:
        # Show the image with drawings
        if image_to_show_continuous is not None:
             cv2.imshow('Image', image_to_show_continuous)
        else: # Fallback
             cv2.imshow('Image', image)

        key = cv2.waitKey(1) & 0xFF

        # Reset the drawing if 'r' is pressed
        if key == ord("r"):
            image_to_show_continuous = clone_continuous.copy() # Reset display image
            contour_points = [] # Clear drawn points
            # mask = np.zeros(image.shape, dtype=np.uint8) # Reset mask if needed (not strictly necessary as it's created fresh)
            is_mouse_pressed = False # Ensure drawing stops if reset mid-drag
            last_point = None
            drag_start_point = None # Also reset this
            # Optionally close the cropped window if it exists
            try:
                cv2.destroyWindow("Freeform Cropped")
            except cv2.error:
                pass # Ignore error if window doesn't exist
            print("Drawing reset.")

        # Quit if 'q' is pressed
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()