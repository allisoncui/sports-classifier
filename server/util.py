import joblib
import json
import numpy as np
import base64
import cv2
from wavelet import w2d

# variables
__class_name_to_number = {}
__class_number_to_name = {}
__model = None

# methods
def classify_image(image_base64_data, file_path=None):
    imgs = get_cropped_image_if_2_eyes(file_path, image_base64_data)
    result = []
    
    for img in imgs:
        scaled_raw_img = cv2.resize(img, (32,32))     # raw image is scaled
        img_har = w2d(img, 'db1', 5)                  # wavelength transformed image
        scaled_img_har = cv2.resize(img_har, (32,32))
        combined_img = np.vstack((scaled_raw_img.reshape(32*32*3,1),scaled_img_har.reshape(32*32,1))) # vertically stack images using numpy
        
        len_image_array = 32*32*3 + 32*32
        final_img = combined_img.reshape(1,len_image_array).astype(float)
        
        result.append({
            'class': class_number_to_name(__model.predict(final_img)[0]),
            'class_probability': list(np.round(__model.predict_proba(final_img)*100,2))[0],
            'class_dictionary': __class_name_to_number
        })                                          
    
    return result

def class_number_to_name(class_num):
    return __class_number_to_name[class_num]

def load_saved_artifacts():
    print("Loading saved artifacts...")
    global __class_name_to_number
    global __class_number_to_name
    
    with open('./server/artifacts/class_dictionary.json', 'r') as file:
        __class_name_to_number = json.load(file)
        __class_number_to_name = {v:k for k,v in __class_name_to_number.items()}
    
    global __model
    if __model is None:
        with open('./server/artifacts/saved_model.pkl', 'rb') as file:
            __model = joblib.load(file)
    print("Loading saved artifacts done")
        
def get_cv2_image_from_base64_string(b64str):           # takes a b64 string and returns cv2 image
    '''
    credit: https://stackoverflow.com/questions/33754935/read-a-base-64-encoded-image-from-memory-using-opencv-python-library
    :param uri:
    :return:
    '''
    encoded_data = b64str.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def get_cropped_image_if_2_eyes(image_path, image_base64_data):
    face_cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_eye.xml')

    if image_path:
        img = cv2.imread(image_path)
    else:
        img = get_cv2_image_from_base64_string(image_base64_data)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    cropped_faces = []
    for (x,y,w,h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = img[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            if len(eyes) >= 2:
                cropped_faces.append(roi_color)
    return cropped_faces

def get_b64_test_image():
    with open("b64.txt") as file:
        return file.read()

if __name__ == '__main__':
    load_saved_artifacts()
    print(classify_image(get_b64_test_image(), None))
    # print(classify_image(None, './test_images/federer1.jpg'))
    # print(classify_image(None, './test_images/federer2.jpg'))
    # print(classify_image(None, './test_images/virat1.jpg'))
    # print(classify_image(None, './test_images/virat2.jpg'))
    # print(classify_image(None, './test_images/virat3.jpg'))