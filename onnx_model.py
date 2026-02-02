import cv2
import numpy as np
import onnxruntime as ort

class YOLOv8_ONNX:
    def __init__(self, model_path):
        # Load the model directly (No PyTorch needed!)
        self.session = ort.InferenceSession(model_path)
        
        # Get model info automatically
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.img_height = self.input_shape[2]
        self.img_width = self.input_shape[3]

    def preprocess(self, image):
        # 1. Resize image to model input
        self.original_height, self.original_width = image.shape[:2]
        img = cv2.resize(image, (self.img_width, self.img_height))
        
        # 2. Convert Color (BGR -> RGB)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 3. Normalize (0-255 -> 0.0-1.0)
        img = img / 255.0
        
        # 4. Transpose (H, W, C) -> (C, H, W) for ONNX
        img = img.transpose(2, 0, 1)
        
        # 5. Add Batch Dimension (1, C, H, W)
        img_input = np.expand_dims(img, axis=0).astype(np.float32)
        return img_input

    def postprocess(self, output, conf_threshold, iou_threshold):
        outputs = np.transpose(np.squeeze(output[0]))
        rows = outputs.shape[0]
        boxes = []
        scores = []
        class_ids = []

        x_factor = self.original_width / self.img_width
        y_factor = self.original_height / self.img_height

        for i in range(rows):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            
            if max_score >= conf_threshold:
                class_id = np.argmax(classes_scores)
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
                
                # Convert to standard (left, top, width, height)
                left = int((x - w / 2) * x_factor)
                top = int((y - h / 2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                
                boxes.append([left, top, width, height])
                scores.append(float(max_score))
                class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, scores, conf_threshold, iou_threshold)

        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                results.append({
                    "box": [x, y, x + w, y + h], 
                    "score": scores[i],   
                    "class_id": class_ids[i] 
                })
        return results

    def predict(self, frame, conf=0.5):
        input_tensor = self.preprocess(frame)
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        detections = self.postprocess(outputs, conf_threshold=conf, iou_threshold=0.45)
        return detections